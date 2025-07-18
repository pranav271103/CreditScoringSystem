# Aave V2 Wallet Credit Scoring System

This project implements a credit scoring system for Aave V2 protocol wallets based on their transaction history. The system analyzes various behavioral patterns from transaction data to assign a credit score between 0 and 1000 to each wallet.

## Features

- Processes raw Aave V2 transaction data
- Extracts relevant features from transaction history
- Calculates credit scores based on transaction behavior
- Generates visualizations of score distribution
- Saves results to CSV files for further analysis

## Prerequisites

- Python 3.8+
- Required Python packages (install using `pip install -r requirements.txt`)

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Place your `user-wallet-transactions.json` file in the project directory

## Usage

Run the credit scoring script:
```
python credit_scoring.py
```

This will generate the following output files:
- `wallet_credit_scores.csv`: Contains wallet addresses and their corresponding credit scores
- `score_distribution.png`: Visualization of credit score distribution
- `score_distribution.csv`: Detailed distribution of credit scores across ranges

## Methodology

The credit scoring system uses the following approach:

1. **Data Loading**: Load and preprocess the transaction data from JSON
2. **Feature Extraction**: Extract relevant features including:
   - Transaction counts (deposits, borrows, repays, liquidations)
   - Transaction frequency and patterns
   - Amount-based metrics (total deposited, borrowed, repaid)
   - Risk indicators (borrow ratio, repayment ratio)

3. **Scoring**: Calculate credit scores based on the extracted features
   - Features are normalized to a common scale
   - A weighted combination of features determines the final score
   - Scores are scaled to the 0-1000 range

4. **Analysis**: Generate visualizations and statistics about the score distribution

## Score Interpretation

- **800-1000**: Excellent credit - responsible borrowing and repayment behavior
- **600-799**: Good credit - generally reliable with minor risk factors
- **400-599**: Fair credit - some risk factors present
- **200-399**: Poor credit - significant risk factors
- **0-199**: Very poor credit - high risk of default or suspicious activity

## Customization

You can adjust the scoring weights in the `calculate_credit_scores` method of the `AaveCreditScorer` class to better suit your risk model.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
