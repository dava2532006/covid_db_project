"""
SEIR and SIR Epidemiological Models for COVID-19
Implements fitting and prediction using scipy
"""
import numpy as np
from scipy.integrate import odeint
from scipy.optimize import minimize
import pandas as pd
from datetime import datetime, timedelta
import json


class SEIRModel:
    """
    SEIR Model: Susceptible-Exposed-Infected-Recovered
    More realistic than SIR - includes incubation period
    
    States:
    - S: Susceptible
    - E: Exposed (infected but not yet infectious)
    - I: Infected (infectious)
    - R: Recovered
    """
    
    def __init__(self, N, beta, sigma, gamma):
        """
        Initialize SEIR model
        
        Args:
            N (int): Total population
            beta (float): Transmission rate (contact rate × transmission probability)
            sigma (float): Rate of progression from E to I (1/incubation_period)
            gamma (float): Recovery rate (1/infectious_period)
        """
        self.N = N
        self.beta = beta
        self.sigma = sigma  # 1/sigma = incubation period
        self.gamma = gamma  # 1/gamma = infectious period
    
    def deriv(self, y, t):
        """Calculate derivatives for SEIR model"""
        S, E, I, R = y
        N = self.N
        
        dSdt = -self.beta * S * I / N
        dEdt = self.beta * S * I / N - self.sigma * E
        dIdt = self.sigma * E - self.gamma * I
        dRdt = self.gamma * I
        
        return dSdt, dEdt, dIdt, dRdt
    
    def solve(self, y0, t):
        """
        Solve SEIR model over time
        
        Args:
            y0: Initial conditions [S0, E0, I0, R0]
            t: Time array
            
        Returns:
            Solution array [S, E, I, R] over time
        """
        solution = odeint(self.deriv, y0, t)
        return solution


class SIRModel:
    """
    SIR Model: Susceptible-Infected-Recovered
    Simpler model - assumes direct progression from S to I
    
    States:
    - S: Susceptible
    - I: Infected (includes incubation + infectious)
    - R: Recovered
    """
    
    def __init__(self, N, beta, gamma):
        """
        Initialize SIR model
        
        Args:
            N (int): Total population
            beta (float): Transmission rate
            gamma (float): Recovery rate (1/infectious_period)
        """
        self.N = N
        self.beta = beta
        self.gamma = gamma
    
    def deriv(self, y, t):
        """Calculate derivatives for SIR model"""
        S, I, R = y
        N = self.N
        
        dSdt = -self.beta * S * I / N
        dIdt = self.beta * S * I / N - self.gamma * I
        dRdt = self.gamma * I
        
        return dSdt, dIdt, dRdt
    
    def solve(self, y0, t):
        """
        Solve SIR model over time
        
        Args:
            y0: Initial conditions [S0, I0, R0]
            t: Time array
            
        Returns:
            Solution array [S, I, R] over time
        """
        solution = odeint(self.deriv, y0, t)
        return solution


class ModelFitter:
    """Fit SEIR/SIR models to actual COVID-19 data"""
    
    @staticmethod
    def fit_seir(confirmed, recovered, population, days=None):
        """
        Fit SEIR model to COVID-19 data
        
        Args:
            confirmed: Array of confirmed cases over time
            recovered: Array of recovered cases over time
            population: Total population
            days: Number of days (if None, infer from data)
            
        Returns:
            dict: Fitted parameters and model statistics
        """
        if days is None:
            days = len(confirmed)
        
        t = np.arange(days)
        
        # Estimate initial conditions
        I0 = confirmed[0] if confirmed[0] > 0 else 1
        R0 = recovered[0] if len(recovered) > 0 else 0
        E0 = max(1, I0 // 2)  # Estimate exposed as half of infected
        S0 = population - I0 - R0 - E0
        
        y0 = [S0, E0, I0, R0]
        
        # Initial parameter estimates (COVID-19 typical values)
        # R0 ≈ 2-3, so beta = R0 * gamma
        gamma = 1/10  # 10-day infectious period
        beta = 0.4 * gamma  # Estimated R0 ≈ 2-3
        sigma = 1/5  # 5-day incubation period
        
        # Define optimization function
        def loss(params):
            beta, sigma, gamma = params
            if any(p <= 0 for p in params):
                return 1e10
            
            model = SEIRModel(population, beta, sigma, gamma)
            solution = model.solve(y0, t)
            I_pred = solution[:len(confirmed), 2]
            
            # Calculate MSE for infected compartment
            mse = np.mean((np.array(confirmed) - I_pred) ** 2)
            return mse
        
        # Optimize parameters
        x0 = [beta, sigma, gamma]
        result = minimize(loss, x0, method='Nelder-Mead')
        
        beta_fit, sigma_fit, gamma_fit = result.x
        
        # Calculate R0
        R0 = beta_fit / gamma_fit
        
        return {
            'model': 'SEIR',
            'beta': float(beta_fit),
            'sigma': float(sigma_fit),
            'gamma': float(gamma_fit),
            'R0': float(R0),
            'incubation_period': float(1/sigma_fit),
            'infectious_period': float(1/gamma_fit),
            'loss': float(result.fun),
            'success': result.success
        }
    
    @staticmethod
    def fit_sir(confirmed, recovered, population, days=None):
        """
        Fit SIR model to COVID-19 data
        
        Args:
            confirmed: Array of confirmed cases over time
            recovered: Array of recovered cases over time
            population: Total population
            days: Number of days
            
        Returns:
            dict: Fitted parameters and model statistics
        """
        if days is None:
            days = len(confirmed)
        
        t = np.arange(days)
        
        # Initial conditions
        I0 = confirmed[0] if confirmed[0] > 0 else 1
        R0 = recovered[0] if len(recovered) > 0 else 0
        S0 = population - I0 - R0
        
        y0 = [S0, I0, R0]
        
        # Initial parameter estimates
        gamma = 1/10  # 10-day infectious period
        beta = 0.4 * gamma
        
        # Optimization function
        def loss(params):
            beta, gamma = params
            if any(p <= 0 for p in params):
                return 1e10
            
            model = SIRModel(population, beta, gamma)
            solution = model.solve(y0, t)
            I_pred = solution[:len(confirmed), 1]
            
            mse = np.mean((np.array(confirmed) - I_pred) ** 2)
            return mse
        
        # Optimize
        x0 = [beta, gamma]
        result = minimize(loss, x0, method='Nelder-Mead')
        
        beta_fit, gamma_fit = result.x
        
        # Calculate R0
        R0 = beta_fit / gamma_fit
        
        return {
            'model': 'SIR',
            'beta': float(beta_fit),
            'gamma': float(gamma_fit),
            'R0': float(R0),
            'infectious_period': float(1/gamma_fit),
            'loss': float(result.fun),
            'success': result.success
        }


def run_example():
    """Example: Fit models to sample COVID-19 data"""
    print("=" * 80)
    print("SEIR/SIR Model Fitting Example - COVID-19")
    print("=" * 80)
    
    # Sample data (Indonesia-like, first 100 days)
    days = 100
    t = np.arange(days)
    
    # Simulated actual data
    population = 270_000_000  # Indonesia population
    
    # Create synthetic data
    model_true = SEIRModel(population, beta=0.0005, sigma=1/5, gamma=1/10)
    S0 = population - 100
    E0 = 50
    I0 = 50
    R0 = 0
    y0_true = [S0, E0, I0, R0]
    
    solution_true = model_true.solve(y0_true, t)
    confirmed_actual = solution_true[:, 2]  # I compartment
    
    print(f"\nPopulation: {population:,}")
    print(f"Time period: {days} days")
    print(f"\nActual data statistics:")
    print(f"  Peak infections: {confirmed_actual.max():.0f}")
    print(f"  Peak day: {confirmed_actual.argmax()}")
    print(f"  Final infections: {confirmed_actual[-1]:.0f}")
    
    # Fit SEIR
    print("\n" + "=" * 80)
    print("Fitting SEIR Model...")
    print("=" * 80)
    seir_fit = ModelFitter.fit_seir(confirmed_actual, np.zeros(days), population, days)
    
    print(f"✓ SEIR Model Fitted:")
    print(f"  β (transmission rate): {seir_fit['beta']:.6f}")
    print(f"  σ (1/incubation period): {seir_fit['sigma']:.6f}")
    print(f"  γ (1/infectious period): {seir_fit['gamma']:.6f}")
    print(f"  R₀ (basic reproduction number): {seir_fit['R0']:.3f}")
    print(f"  Incubation period: {seir_fit['incubation_period']:.1f} days")
    print(f"  Infectious period: {seir_fit['infectious_period']:.1f} days")
    print(f"  Loss (MSE): {seir_fit['loss']:.2e}")
    
    # Fit SIR
    print("\n" + "=" * 80)
    print("Fitting SIR Model...")
    print("=" * 80)
    sir_fit = ModelFitter.fit_sir(confirmed_actual, np.zeros(days), population, days)
    
    print(f"✓ SIR Model Fitted:")
    print(f"  β (transmission rate): {sir_fit['beta']:.6f}")
    print(f"  γ (1/infectious period): {sir_fit['gamma']:.6f}")
    print(f"  R₀ (basic reproduction number): {sir_fit['R0']:.3f}")
    print(f"  Infectious period: {sir_fit['infectious_period']:.1f} days")
    print(f"  Loss (MSE): {sir_fit['loss']:.2e}")
    
    # Compare predictions
    print("\n" + "=" * 80)
    print("Model Predictions Comparison")
    print("=" * 80)
    
    model_seir = SEIRModel(population, **{k: seir_fit[k] for k in ['beta', 'sigma', 'gamma']})
    model_sir = SIRModel(population, **{k: sir_fit[k] for k in ['beta', 'gamma']})
    
    pred_seir = model_seir.solve(y0_true, t)
    pred_sir = model_sir.solve([S0, I0, R0], t)
    
    I_seir = pred_seir[:, 2]
    I_sir = pred_sir[:, 1]
    
    mae_seir = np.mean(np.abs(confirmed_actual - I_seir))
    mae_sir = np.mean(np.abs(confirmed_actual - I_sir))
    rmse_seir = np.sqrt(np.mean((confirmed_actual - I_seir) ** 2))
    rmse_sir = np.sqrt(np.mean((confirmed_actual - I_sir) ** 2))
    
    print(f"\nSEIR Model:")
    print(f"  MAE (Mean Absolute Error): {mae_seir:.0f}")
    print(f"  RMSE (Root Mean Square Error): {rmse_seir:.0f}")
    print(f"  Peak prediction: {I_seir.max():.0f} (actual: {confirmed_actual.max():.0f})")
    
    print(f"\nSIR Model:")
    print(f"  MAE (Mean Absolute Error): {mae_sir:.0f}")
    print(f"  RMSE (Root Mean Square Error): {rmse_sir:.0f}")
    print(f"  Peak prediction: {I_sir.max():.0f} (actual: {confirmed_actual.max():.0f})")
    
    print(f"\n✓ SEIR is {'more' if mae_seir < mae_sir else 'less'} accurate than SIR")
    print("=" * 80)


if __name__ == "__main__":
    run_example()
