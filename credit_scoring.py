import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List

class AaveCreditScorer:
    def __init__(self, data_path):
        """
        Initialize the AaveCreditScorer with the path to the transaction data.
        
        Args:
            data_path (str): Path to the JSON file containing transaction data
        """
        self.data_path = data_path
        self.transactions = None
        self.wallet_features = None
        self.scaler = MinMaxScaler()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        
    def extract_action_data(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant fields from the nested actionData."""
        result = {}
        if not isinstance(action_data, dict):
            return result
            
        # Extract common fields
        result['amount'] = float(action_data.get('amount', 0))
        result['asset'] = action_data.get('asset', '')
        
        # Handle different action types
        if 'borrowRateMode' in action_data:
            result['borrowRateMode'] = action_data['borrowRateMode']
            result['borrowRate'] = float(action_data.get('borrowRate', 0))
            
        if 'repayAmount' in action_data:
            result['repayAmount'] = float(action_data.get('repayAmount', 0))
            
        if 'liquidatedCollateralAmount' in action_data:
            result['liquidatedCollateralAmount'] = float(action_data.get('liquidatedCollateralAmount', 0))
            result['liquidatedUser'] = action_data.get('liquidatedUser', '')
            
        return result

    def load_data(self) -> pd.DataFrame:
        """Load and preprocess the transaction data."""
        print("Loading transaction data...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.transactions = json.load(f)
        
        # Process transactions to extract relevant data
        processed_data = []
        for tx in self.transactions:
            if not isinstance(tx, dict):
                continue
                
            # Extract base fields
            tx_data = {
                'user': tx.get('userWallet', '').lower(),
                'tx_hash': tx.get('txHash', ''),
                'timestamp': pd.to_datetime(tx.get('timestamp', '1970-01-01')),
                'block_number': int(tx.get('blockNumber', 0)),
                'action': tx.get('action', '').lower(),
                'protocol': tx.get('protocol', '').lower()
            }
            
            # Extract action-specific data
            action_data = tx.get('actionData', {})
            if isinstance(action_data, dict):
                tx_data.update(self.extract_action_data(action_data))
            
            processed_data.append(tx_data)
        
        # Convert to DataFrame
        df = pd.DataFrame(processed_data)
        
        # Convert timestamp to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract relevant features from transaction data."""
        print("Extracting features...")
        
        if df.empty:
            raise ValueError("No transaction data available for feature extraction")
        
        # Group by user and extract features
        features = []
        
        for user, group in df.groupby('user'):
            if not isinstance(user, str):
                continue
                
            # Basic transaction counts by action type
            tx_count = len(group)
            action_counts = group['action'].value_counts().to_dict()
            
            # Time-based features
            time_diff = (group['timestamp'].max() - group['timestamp'].min()).total_seconds() / 3600  # in hours
            tx_frequency = tx_count / (time_diff + 1)  # transactions per hour
            
            # Amount-based features
            total_deposited = group[group['action'] == 'deposit']['amount'].sum()
            total_borrowed = group[group['action'] == 'borrow']['amount'].sum()
            total_repaid = group[group['action'] == 'repay']['amount'].sum()
            total_liquidated = group[group['action'] == 'liquidation']['amount'].sum()
            
            # Risk indicators
            borrow_ratio = total_borrowed / (total_deposited + 1e-10)
            repayment_ratio = total_repaid / (total_borrowed + 1e-10)
            
            # Additional metrics
            unique_assets = group['asset'].nunique()
            avg_tx_amount = group['amount'].mean() if not group['amount'].empty else 0
            
            features.append({
                'user': user,
                'tx_count': tx_count,
                'deposit_count': action_counts.get('deposit', 0),
                'borrow_count': action_counts.get('borrow', 0),
                'repay_count': action_counts.get('repay', 0),
                'liquidation_count': action_counts.get('liquidation', 0),
                'tx_frequency': tx_frequency,
                'total_deposited': total_deposited,
                'total_borrowed': total_borrowed,
                'total_repaid': total_repaid,
                'total_liquidated': total_liquidated,
                'borrow_ratio': min(borrow_ratio, 1000),  # Cap at 1000x
                'repayment_ratio': min(repayment_ratio, 10),  # Cap at 10x
                'activity_duration_hours': max(time_diff, 0.1),  # Minimum 0.1 hours
                'unique_assets': unique_assets,
                'avg_tx_amount': avg_tx_amount
            })
        
        self.wallet_features = pd.DataFrame(features)
        return self.wallet_features
    
    def calculate_credit_scores(self):
        """Calculate credit scores based on the extracted features."""
        if self.wallet_features is None:
            raise ValueError("Please run extract_features() first")
        
        print("Calculating credit scores...")
        
        # Feature matrix (exclude user column)
        X = self.wallet_features.drop('user', axis=1)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train a simple model (in a real scenario, this would be more sophisticated)
        # Here we're using the sum of normalized features as a simple scoring mechanism
        scores = X_scaled.sum(axis=1)
        
        # Scale scores to 0-1000 range
        min_score, max_score = scores.min(), scores.max()
        credit_scores = 1000 * (scores - min_score) / (max_score - min_score)
        
        # Assign scores back to the dataframe
        self.wallet_features['credit_score'] = credit_scores
        
        return self.wallet_features[['user', 'credit_score']]
    
    def analyze_scores(self, scores_df):
        """Analyze the distribution of credit scores."""
        print("Analyzing score distribution...")
        
        # Create score ranges
        bins = list(range(0, 1001, 100))
        labels = [f"{i}-{i+99}" for i in range(0, 1000, 100)]
        scores_df['score_range'] = pd.cut(scores_df['credit_score'], bins=bins, labels=labels, right=False)
        
        # Calculate distribution
        distribution = scores_df['score_range'].value_counts().sort_index()
        
        # Plot distribution
        plt.figure(figsize=(12, 6))
        sns.barplot(x=distribution.index, y=distribution.values)
        plt.title('Credit Score Distribution')
        plt.xlabel('Credit Score Range')
        plt.ylabel('Number of Wallets')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('score_distribution.png')
        plt.close()
        
        return distribution

def main():
    # Initialize the scorer with the data path
    data_file = 'user-wallet-transactions.json'
    print(f"Starting credit scoring with data file: {data_file}")
    
    try:
        scorer = AaveCreditScorer(data_file)
        
        # Load and preprocess data
        print("\nStep 1: Loading and preprocessing data...")
        df = scorer.load_data()
        print(f"Loaded {len(df)} transactions for {df['user'].nunique()} unique wallets")
        
        if df.empty:
            raise ValueError("No valid transaction data found in the input file")
        
        # Extract features
        print("\nStep 2: Extracting features...")
        features = scorer.extract_features(df)
        print(f"Extracted features for {len(features)} wallets")
        
        # Calculate credit scores
        print("\nStep 3: Calculating credit scores...")
        scores = scorer.calculate_credit_scores()
        
        # Analyze score distribution
        print("\nStep 4: Analyzing score distribution...")
        distribution = scorer.analyze_scores(scores)
        
        # Save results
        print("\nSaving results...")
        scores.to_csv('wallet_credit_scores.csv', index=False)
        distribution.to_csv('score_distribution.csv')
        
        print("\nCredit scoring completed successfully!")
        print(f"Processed {len(scores)} wallets.")
        print("Results saved to 'wallet_credit_scores.csv' and 'score_distribution.csv'")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    main()
