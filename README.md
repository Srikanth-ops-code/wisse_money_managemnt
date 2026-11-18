# WISE Flask Product Demo

A local, interactive prototype of WISE — Smart Money Management with Virtual Pots.

## Features
- Dashboard with main balance, available balance, pot allocation and Save Vault
- Create virtual pots
- Add money to a pot (demo automatically moves 2% of each top-up into Save Vault)
- Record spending from a selected pot
- Simulated external bank account linking and transfer
- Spending insights and illustrative bank-growth dashboard
- Reset demo data

## Important demo limitations
This is a **simulation only**. It does not connect to real banks, UPI, cards, payment networks or customer accounts. External bank linking and transfers are simulated. Do not enter real banking credentials or personal financial information. The 2% micro-savings rate and seeded balances are illustrative and configurable in `app.py`.

## Run on Windows (PowerShell)

1. Install Python 3.10 or newer.
2. Extract the ZIP file and open PowerShell in the `wise_flask_demo` folder.
3. Create a virtual environment:

   ```powershell
   py -m venv venv
   ```

4. Activate it:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```

5. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Start the app:

   ```powershell
   python app.py
   ```

7. Open this address in your browser:

   `http://127.0.0.1:5000`

## Demo flow for your presentation
1. Show the dashboard and explain the main balance versus money allocated to pots.
2. Add money to Travel or Food. Show the automatic 2% Save Vault contribution.
3. Record a purchase from that pot and show the updated balance.
4. Open Spending Insights to show category-wise spend.
5. Open External Bank to simulate linking a non-WISE bank account and moving demo funds.
6. Open Bank Growth to explain the illustrative deposit opportunity.
7. Use Reset Demo to restore the sample data before another presentation.

## Reset
Use the **Reset demo data** button in the navigation. It restores the sample balances and transactions.
