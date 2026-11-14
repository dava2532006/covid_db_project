"""
SEIR/SIR Models with Intervention Scenarios
Predicts impact of delayed vaccination and other interventions
"""
import json
from datetime import datetime
from seir_sir_simple import SEIRSimple, SIRSimple, SimpleTimeStepper


class InterventionSEIR:
    """SEIR model with vaccination intervention"""
    
    def __init__(self, N, beta, sigma, gamma, vaccination_rate=0, vaccination_start_day=0):
        """
        Args:
            N: Population
            beta: Transmission rate
            sigma: 1/incubation period
            gamma: 1/recovery period
            vaccination_rate: Daily vaccination rate (fraction of S vaccinated per day)
            vaccination_start_day: Day when vaccination starts
        """
        self.N = N
        self.beta = beta
        self.sigma = sigma
        self.gamma = gamma
        self.vaccination_rate = vaccination_rate
        self.vaccination_start_day = vaccination_start_day
    
    def deriv(self, y, t):
        """SEIR derivatives with vaccination"""
        S, E, I, R = y
        N = self.N
        
        # Vaccination effect (moves S → R directly)
        vaccination = 0
        if t >= self.vaccination_start_day:
            vaccination = self.vaccination_rate * S
        
        dSdt = -self.beta * S * I / N - vaccination
        dEdt = self.beta * S * I / N - self.sigma * E
        dIdt = self.sigma * E - self.gamma * I
        dRdt = self.gamma * I + vaccination
        
        return [dSdt, dEdt, dIdt, dRdt]
    
    def solve(self, y0, t_end):
        """Solve SEIR with intervention"""
        return SimpleTimeStepper.solve(self.deriv, y0, 0, t_end, steps=1000)


def compare_vaccination_delays(
    population,
    initial_infected,
    vaccination_rate,
    no_intervention_days,
    delay_days_list,
    forecast_days=365
):
    """
    Compare impact of vaccination delays
    
    Args:
        population: Total population
        initial_infected: Initial infected cases
        vaccination_rate: Daily vaccination rate (e.g., 0.01 = 1% of susceptible per day)
        no_intervention_days: Days to run without intervention (baseline)
        delay_days_list: List of delay days to compare (e.g., [0, 7, 14, 30, 60])
        forecast_days: Total days to simulate
    
    Returns:
        dict with results for each scenario
    """
    
    # Initial conditions
    S0 = population - initial_infected
    E0 = initial_infected // 2
    I0 = initial_infected // 2
    R0 = 0
    y0 = [S0, E0, I0, R0]
    
    # COVID-19 parameters
    beta = 0.0005
    sigma = 1/5    # 5-day incubation
    gamma = 1/10   # 10-day recovery
    
    results = {}
    
    # Scenario 1: No intervention (baseline)
    print(f"\n[Scenario 1] No Vaccination (Baseline)")
    model_baseline = SEIRSimple(population, beta, sigma, gamma)
    sol_baseline = model_baseline.solve(y0, forecast_days)
    infected_baseline = [sol[2] for sol in sol_baseline]
    
    peak_baseline = max(infected_baseline)
    peak_day_baseline = infected_baseline.index(peak_baseline)
    total_infected_baseline = sol_baseline[-1][3]  # Final R
    
    results['baseline'] = {
        'scenario': 'No Vaccination',
        'delay_days': None,
        'peak_infections': int(peak_baseline),
        'peak_day': peak_day_baseline,
        'total_infected': int(total_infected_baseline),
        'predictions': infected_baseline[:forecast_days]
    }
    
    print(f"  Peak infections: {peak_baseline:,.0f}")
    print(f"  Peak day: {peak_day_baseline}")
    print(f"  Total infected: {total_infected_baseline:,.0f}")
    
    # Scenario 2+: Vaccination with different delays
    for idx, delay in enumerate(delay_days_list, start=2):
        vaccination_start = no_intervention_days + delay
        
        print(f"\n[Scenario {idx}] Vaccination starts on Day {vaccination_start} (Delay: {delay} days)")
        
        model_delayed = InterventionSEIR(
            population, beta, sigma, gamma,
            vaccination_rate=vaccination_rate,
            vaccination_start_day=vaccination_start
        )
        
        sol_delayed = model_delayed.solve(y0, forecast_days)
        infected_delayed = [sol[2] for sol in sol_delayed]
        
        peak_delayed = max(infected_delayed)
        peak_day_delayed = infected_delayed.index(peak_delayed)
        total_infected_delayed = sol_delayed[-1][3]  # Final R
        
        # Calculate impact
        additional_infections = total_infected_delayed - total_infected_baseline
        peak_increase = peak_delayed - peak_baseline
        
        results[f'delay_{delay}'] = {
            'scenario': f'Vaccination Day {vaccination_start}',
            'delay_days': delay,
            'vaccination_start': vaccination_start,
            'peak_infections': int(peak_delayed),
            'peak_day': peak_day_delayed,
            'total_infected': int(total_infected_delayed),
            'additional_infections': int(additional_infections),
            'peak_increase': int(peak_increase),
            'predictions': infected_delayed[:forecast_days]
        }
        
        print(f"  Peak infections: {peak_delayed:,.0f} (+{peak_increase:,.0f} vs baseline)")
        print(f"  Peak day: {peak_day_delayed}")
        print(f"  Total infected: {total_infected_delayed:,.0f}")
        print(f"  Additional infections due to delay: {additional_infections:,.0f}")
    
    return results


def calculate_lives_saved(baseline_deaths, scenario_deaths, death_rate=0.02):
    """
    Calculate lives saved by early intervention
    
    Args:
        baseline_deaths: Deaths without intervention
        scenario_deaths: Deaths with intervention
        death_rate: Case fatality rate (default 2%)
    
    Returns:
        Lives saved
    """
    return max(0, baseline_deaths - scenario_deaths)


def run_vaccination_delay_analysis():
    """Main analysis: Impact of vaccination delays"""
    
    print("=" * 80)
    print("VACCINATION DELAY IMPACT ANALYSIS - COVID-19 SEIR Model")
    print("=" * 80)
    
    # Parameters
    population = 270_000_000  # Indonesia
    initial_infected = 1000
    vaccination_rate = 0.005  # 0.5% of susceptible vaccinated per day
    no_intervention_days = 50  # Start considering vaccination after 50 days
    delay_scenarios = [0, 7, 14, 30, 60, 90]  # Delay in days
    forecast_days = 365
    
    print(f"\nSimulation Parameters:")
    print(f"  Population: {population:,}")
    print(f"  Initial infected: {initial_infected:,}")
    print(f"  Vaccination rate: {vaccination_rate*100:.1f}% per day")
    print(f"  Baseline vaccination start: Day {no_intervention_days}")
    print(f"  Delay scenarios: {delay_scenarios} days")
    print(f"  Forecast period: {forecast_days} days")
    
    # Run comparison
    results = compare_vaccination_delays(
        population=population,
        initial_infected=initial_infected,
        vaccination_rate=vaccination_rate,
        no_intervention_days=no_intervention_days,
        delay_days_list=delay_scenarios,
        forecast_days=forecast_days
    )
    
    # Summary table
    print("\n" + "=" * 80)
    print("SUMMARY: Impact of Vaccination Delays")
    print("=" * 80)
    
    print(f"\n{'Scenario':<30} {'Delay':<10} {'Peak':<15} {'Total Infected':<20} {'Additional':<15}")
    print("-" * 95)
    
    baseline_total = results['baseline']['total_infected']
    
    for key, data in results.items():
        scenario = data['scenario']
        delay = f"{data['delay_days']} days" if data['delay_days'] is not None else "N/A"
        peak = f"{data['peak_infections']:,}"
        total = f"{data['total_infected']:,}"
        additional = f"+{data.get('additional_infections', 0):,}" if 'additional_infections' in data else "-"
        
        print(f"{scenario:<30} {delay:<10} {peak:<15} {total:<20} {additional:<15}")
    
    # Death estimates (assuming 2% CFR)
    cfr = 0.02
    print(f"\n" + "=" * 80)
    print(f"ESTIMATED DEATHS (assuming {cfr*100}% Case Fatality Rate)")
    print("=" * 80)
    
    baseline_deaths = int(baseline_total * cfr)
    print(f"\nBaseline (no vaccination): {baseline_deaths:,} deaths")
    
    for key, data in results.items():
        if key == 'baseline':
            continue
        
        scenario_deaths = int(data['total_infected'] * cfr)
        additional_deaths = scenario_deaths - baseline_deaths
        lives_lost_per_day = additional_deaths / data['delay_days'] if data['delay_days'] > 0 else 0
        
        print(f"\n{data['scenario']}:")
        print(f"  Total deaths: {scenario_deaths:,}")
        print(f"  Additional deaths: +{additional_deaths:,}")
        print(f"  Lives lost per day of delay: ~{lives_lost_per_day:,.0f}")
    
    # Key insights
    print(f"\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    
    # Compare immediate vs 30-day delay
    if 'delay_0' in results and 'delay_30' in results:
        immediate = results['delay_0']
        delayed_30 = results['delay_30']
        
        diff_infections = delayed_30['additional_infections'] - immediate.get('additional_infections', 0)
        diff_deaths = int(diff_infections * cfr)
        
        print(f"\n✓ Delaying vaccination by 30 days results in:")
        print(f"  - {diff_infections:,} additional infections")
        print(f"  - ~{diff_deaths:,} additional deaths")
        print(f"  - Peak increases by {delayed_30['peak_increase']:,} cases")
        
        print(f"\n✓ Every week of delay costs approximately:")
        weekly_infections = diff_infections / 4
        weekly_deaths = diff_deaths / 4
        print(f"  - {weekly_infections:,.0f} additional infections")
        print(f"  - ~{weekly_deaths:,.0f} additional deaths")
    
    print(f"\n" + "=" * 80)
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'population': population,
            'initial_infected': initial_infected,
            'vaccination_rate': vaccination_rate,
            'no_intervention_days': no_intervention_days,
            'forecast_days': forecast_days,
            'death_rate': cfr
        },
        'scenarios': results
    }
    
    with open('vaccination_delay_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Results saved to: vaccination_delay_analysis.json")
    
    return results


if __name__ == "__main__":
    run_vaccination_delay_analysis()
