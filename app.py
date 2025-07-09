import csv
from io import StringIO
import time
from flask import Flask, render_template, request, redirect, send_file, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
import requests
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling
import google.generativeai as genai
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from decimal import Decimal

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Google GenAI API securely
genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY", "AIzaSyAJIzmuTpZbQRD-P-RU7CVe4HlbnOYlYB0"))
client = genai.GenerativeModel('gemini-1.5-flash')

# Fi MCP Server Configuration
FI_MCP_CONFIG = {
    'base_url': os.getenv('FI_MCP_BASE_URL', 'https://api.fimoney.com/mcp'),
    'api_key': os.getenv('FI_MCP_API_KEY', ''),
    'version': 'v1'
}

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Kiran08062004'),
    'database': os.getenv('DB_NAME', 'finance_app_ai')
}

# Create a connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="finance_app_ai_pool",
    pool_size=10,
    **DB_CONFIG
)

# Fi MCP Data Models
@dataclass
class FinancialProfile:
    user_id: str
    net_worth: float
    total_assets: float
    total_liabilities: float
    credit_score: int
    monthly_income: float
    monthly_expenses: float
    investment_portfolio: Dict[str, Any]
    insurance_policies: List[Dict[str, Any]]
    loans: List[Dict[str, Any]]
    epf_balance: float
    last_updated: datetime.datetime

@dataclass
class InvestmentAnalysis:
    portfolio_value: float
    returns_ytd: float
    risk_score: float
    diversification_score: float
    underperforming_funds: List[Dict[str, Any]]
    top_performing_funds: List[Dict[str, Any]]
    recommendations: List[str]

# Fi MCP Server Integration
class FiMCPClient:
    def __init__(self, config: Dict[str, str]):
        self.base_url = config['base_url']
        self.api_key = config['api_key']
        self.version = config['version']
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-API-Version': self.version
        }

    def get_financial_profile(self, user_id: str) -> Optional[FinancialProfile]:
        """Fetch comprehensive financial profile from Fi MCP"""
        try:
            response = requests.get(
                f"{self.base_url}/profile/{user_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return FinancialProfile(
                user_id=user_id,
                net_worth=data.get('net_worth', 0),
                total_assets=data.get('total_assets', 0),
                total_liabilities=data.get('total_liabilities', 0),
                credit_score=data.get('credit_score', 750),
                monthly_income=data.get('monthly_income', 0),
                monthly_expenses=data.get('monthly_expenses', 0),
                investment_portfolio=data.get('investment_portfolio', {}),
                insurance_policies=data.get('insurance_policies', []),
                loans=data.get('loans', []),
                epf_balance=data.get('epf_balance', 0),
                last_updated=datetime.datetime.now()
            )
        except Exception as e:
            logger.error(f"Error fetching financial profile: {str(e)}")
            return None

    def get_investment_analysis(self, user_id: str) -> Optional[InvestmentAnalysis]:
        """Get detailed investment analysis from Fi MCP"""
        try:
            response = requests.get(
                f"{self.base_url}/investments/analysis/{user_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return InvestmentAnalysis(
                portfolio_value=data.get('portfolio_value', 0),
                returns_ytd=data.get('returns_ytd', 0),
                risk_score=data.get('risk_score', 5),
                diversification_score=data.get('diversification_score', 5),
                underperforming_funds=data.get('underperforming_funds', []),
                top_performing_funds=data.get('top_performing_funds', []),
                recommendations=data.get('recommendations', [])
            )
        except Exception as e:
            logger.error(f"Error fetching investment analysis: {str(e)}")
            return None

    def get_loan_eligibility(self, user_id: str, loan_amount: float, loan_type: str) -> Dict[str, Any]:
        """Check loan eligibility using Fi MCP"""
        try:
            payload = {
                'user_id': user_id,
                'loan_amount': loan_amount,
                'loan_type': loan_type
            }
            response = requests.post(
                f"{self.base_url}/loans/eligibility",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error checking loan eligibility: {str(e)}")
            return {'eligible': False, 'reason': 'Unable to process request'}

    def get_financial_forecast(self, user_id: str, target_age: int) -> Dict[str, Any]:
        """Get financial forecast using Fi MCP"""
        try:
            response = requests.get(
                f"{self.base_url}/forecast/{user_id}?target_age={target_age}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching financial forecast: {str(e)}")
            return {}

# Initialize Fi MCP Client
fi_mcp_client = FiMCPClient(FI_MCP_CONFIG)

# Enhanced AI Financial Agent
class FinancialAIAgent:
    def __init__(self):
        self.client = client
        self.fi_mcp = fi_mcp_client
        
    def get_financial_context(self, user_id: str) -> str:
        """Get comprehensive financial context for AI processing"""
        profile = self.fi_mcp.get_financial_profile(user_id)
        investment_analysis = self.fi_mcp.get_investment_analysis(user_id)
        
        if not profile:
            return "No financial data available"
        
        context = f"""
        User Financial Profile:
        - Net Worth: ₹{profile.net_worth:,.2f}
        - Total Assets: ₹{profile.total_assets:,.2f}
        - Total Liabilities: ₹{profile.total_liabilities:,.2f}
        - Credit Score: {profile.credit_score}
        - Monthly Income: ₹{profile.monthly_income:,.2f}
        - Monthly Expenses: ₹{profile.monthly_expenses:,.2f}
        - EPF Balance: ₹{profile.epf_balance:,.2f}
        - Investment Portfolio Value: ₹{profile.investment_portfolio.get('total_value', 0):,.2f}
        - Active Loans: {len(profile.loans)}
        - Insurance Policies: {len(profile.insurance_policies)}
        """
        
        if investment_analysis:
            context += f"""
        
        Investment Analysis:
        - Portfolio Value: ₹{investment_analysis.portfolio_value:,.2f}
        - YTD Returns: {investment_analysis.returns_ytd:.2f}%
        - Risk Score: {investment_analysis.risk_score}/10
        - Diversification Score: {investment_analysis.diversification_score}/10
        - Underperforming Funds: {len(investment_analysis.underperforming_funds)}
        - Top Performing Funds: {len(investment_analysis.top_performing_funds)}
        """
        
        return context

    def process_financial_query(self, user_id: str, query: str, context_type: str = "general") -> str:
        """Process financial queries with personalized data"""
        try:
            financial_context = self.get_financial_context(user_id)
            
            system_prompt = f"""
            You are a highly skilled personal finance advisor with access to the user's complete financial profile.
            You provide personalized, actionable financial advice based on real data.
            
            User's Financial Data:
            {financial_context}
            
            Guidelines:
            1. Use the actual financial data provided to give personalized advice
            2. Be specific with numbers and calculations
            3. Provide actionable recommendations
            4. Consider the user's complete financial picture
            5. Highlight risks and opportunities
            6. Use Indian financial context (INR, Indian investment options, etc.)
            7. Be conversational but professional
            
            User Query: {query}
            
            Provide a comprehensive, personalized response based on their actual financial situation.
            """
            
            response = self.client.generate_content(system_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error processing financial query: {str(e)}")
            return "I apologize, but I'm unable to process your financial query at the moment. Please try again later."

    def analyze_investment_performance(self, user_id: str) -> str:
        """Analyze investment performance with specific recommendations"""
        try:
            analysis = self.fi_mcp.get_investment_analysis(user_id)
            if not analysis:
                return "Unable to fetch investment analysis at the moment."
            
            prompt = f"""
            Analyze this investment portfolio performance and provide specific recommendations:
            
            Portfolio Value: ₹{analysis.portfolio_value:,.2f}
            YTD Returns: {analysis.returns_ytd:.2f}%
            Risk Score: {analysis.risk_score}/10
            Diversification Score: {analysis.diversification_score}/10
            
            Underperforming Funds: {json.dumps(analysis.underperforming_funds, indent=2)}
            Top Performing Funds: {json.dumps(analysis.top_performing_funds, indent=2)}
            
            Provide:
            1. Performance assessment
            2. Specific actions to take
            3. Risk analysis
            4. Diversification recommendations
            5. Tax implications if any
            """
            
            response = self.client.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing investment performance: {str(e)}")
            return "Unable to analyze investment performance at the moment."

    def check_loan_affordability(self, user_id: str, loan_amount: float, loan_type: str) -> str:
        """Check loan affordability with personalized analysis"""
        try:
            profile = self.fi_mcp.get_financial_profile(user_id)
            eligibility = self.fi_mcp.get_loan_eligibility(user_id, loan_amount, loan_type)
            
            if not profile:
                return "Unable to fetch your financial profile for loan analysis."
            
            prompt = f"""
            Analyze loan affordability for this user:
            
            Loan Details:
            - Amount: ₹{loan_amount:,.2f}
            - Type: {loan_type}
            
            User's Financial Profile:
            - Monthly Income: ₹{profile.monthly_income:,.2f}
            - Monthly Expenses: ₹{profile.monthly_expenses:,.2f}
            - Credit Score: {profile.credit_score}
            - Net Worth: ₹{profile.net_worth:,.2f}
            - Current Loans: {len(profile.loans)}
            
            Eligibility Check Result: {json.dumps(eligibility, indent=2)}
            
            Provide:
            1. Affordability analysis
            2. EMI impact on monthly budget
            3. Alternative loan options if needed
            4. Steps to improve eligibility if rejected
            5. Risk assessment
            """
            
            response = self.client.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error checking loan affordability: {str(e)}")
            return "Unable to analyze loan affordability at the moment."

    def financial_forecast(self, user_id: str, target_age: int) -> str:
        """Provide financial forecast to target age"""
        try:
            forecast = self.fi_mcp.get_financial_forecast(user_id, target_age)
            profile = self.fi_mcp.get_financial_profile(user_id)
            
            if not forecast or not profile:
                return "Unable to generate financial forecast at the moment."
            
            prompt = f"""
            Generate a comprehensive financial forecast:
            
            Current Financial Status:
            - Current Age: {profile.get('age', 'N/A')}
            - Target Age: {target_age}
            - Current Net Worth: ₹{profile.net_worth:,.2f}
            - Monthly Income: ₹{profile.monthly_income:,.2f}
            - Monthly Expenses: ₹{profile.monthly_expenses:,.2f}
            
            Forecast Data: {json.dumps(forecast, indent=2)}
            
            Provide:
            1. Projected wealth at target age
            2. Monthly savings required to meet goals
            3. Investment strategy recommendations
            4. Risk factors and mitigation
            5. Retirement readiness assessment
            6. Action plan with timelines
            """
            
            response = self.client.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating financial forecast: {str(e)}")
            return "Unable to generate financial forecast at the moment."

# Initialize AI Agent
ai_agent = FinancialAIAgent()

# Database Helper Functions
def get_db_connection():
    return db_pool.get_connection()

def execute_query(query, params=None, fetch=None):
    """Execute SQL query with optional parameters"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(query, params or ())
        
        if fetch == 'one':
            result = cursor.fetchone()
        elif fetch == 'all':
            result = cursor.fetchall()
        else:
            connection.commit()
            result = None
            
        return result
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

# Enhanced User Helper Functions
def save_user(data):
    query = """
    INSERT INTO users 
    (email, password, name, dob, annual_income, phone, family_name, family_members, country, 
     family_username, family_password, fi_user_id, ai_enabled, data_sync_enabled)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data['email'], data['password'], data['name'], data['dob'], data['annual_income'],
        data['phone'], data['family_name'], data['family_members'], data['country'],
        data['family_username'], data['family_password'], data.get('fi_user_id', ''),
        data.get('ai_enabled', True), data.get('data_sync_enabled', True)
    )
    execute_query(query, params)

def get_user(email):
    query = "SELECT * FROM users WHERE email = %s"
    return execute_query(query, (email,), 'one')

def update_user_fi_id(email, fi_user_id):
    """Update user's Fi MCP user ID"""
    query = "UPDATE users SET fi_user_id = %s WHERE email = %s"
    execute_query(query, (fi_user_id, email))

def save_ai_conversation(user_email, query, response, context_type="general"):
    """Save AI conversation for analytics and improvement"""
    query_sql = """
    INSERT INTO ai_conversations (user_email, query, response, context_type, timestamp)
    VALUES (%s, %s, %s, %s, %s)
    """
    execute_query(query_sql, (user_email, query, response, context_type, datetime.datetime.now()))

def get_user_conversations(user_email, limit=10):
    """Get recent AI conversations for context"""
    query = """
    SELECT query, response, context_type, timestamp
    FROM ai_conversations
    WHERE user_email = %s
    ORDER BY timestamp DESC
    LIMIT %s
    """
    return execute_query(query, (user_email, limit), 'all')

# Enhanced Routes

@app.before_request
def check_login():
    allowed_routes = ['login', 'register', 'static', 'health_check']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect(url_for('login'))

@app.route('/health_check')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form
        if get_user(form['email']):
            return render_template('register.html', error="Email is already registered.")

        family_username = form['family_name'].lower().replace(' ', '') + '_fam'
        family_password = form['family_name'][:3].lower() + form['phone'][-4:]

        user_data = {
            'name': form['name'],
            'dob': form['dob'],
            'annual_income': form['annual_income'],
            'email': form['email'],
            'password': generate_password_hash(form['password']),
            'phone': form['phone'],
            'family_name': form['family_name'],
            'family_members': form['family_members'],
            'country': form['country'],
            'family_username': family_username,
            'family_password': family_password,
            'fi_user_id': form.get('fi_user_id', ''),
            'ai_enabled': form.get('ai_enabled', 'on') == 'on',
            'data_sync_enabled': form.get('data_sync_enabled', 'on') == 'on'
        }

        save_user(user_data)
        session['email'] = user_data['email']
        
        if int(form['family_members']) > 1:
            return redirect(url_for('family_details'))
        
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form['login_type']
        if login_type == 'individual':
            user = get_user(request.form['email'])
            if user and check_password_hash(user['password'], request.form['password']):
                session['email'] = user['email']
                session['fi_user_id'] = user.get('fi_user_id', '')
                return redirect(url_for('dashboard'))
            return render_template('login.html', error="Invalid email or password.")
        
        elif login_type == 'family':
            family_user = get_user_by_family_username(request.form['family_username'])
            if family_user and family_user['family_password'] == request.form['family_password']:
                session['email'] = family_user['email']
                session['fi_user_id'] = family_user.get('fi_user_id', '')
                return redirect(url_for('dashboard'))
            return render_template('login.html', error="Invalid family username or password.")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user = get_user(session['email'])
    has_family = has_family_members(session['email'])
    
    # Get Fi MCP financial profile if available
    fi_profile = None
    if user.get('fi_user_id'):
        fi_profile = fi_mcp_client.get_financial_profile(user['fi_user_id'])
    
    return render_template('dashboard.html',
                           name=user['name'],
                           annual_income=float(user['annual_income']),
                           has_family=has_family,
                           fi_profile=fi_profile,
                           ai_enabled=user.get('ai_enabled', True))

# AI Agent Routes

@app.route('/ai-chat')
def ai_chat():
    """AI Chat interface"""
    user = get_user(session['email'])
    recent_conversations = get_user_conversations(session['email'], 5)
    return render_template('ai_chat.html', 
                         user=user, 
                         conversations=recent_conversations)

@app.route('/ai-query', methods=['POST'])
def ai_query():
    """Process AI financial queries"""
    try:
        data = request.json
        query = data.get('query', '')
        context_type = data.get('context_type', 'general')
        
        user = get_user(session['email'])
        fi_user_id = user.get('fi_user_id', '')
        
        if not fi_user_id:
            response = "Please connect your Fi account to get personalized financial insights."
        else:
            response = ai_agent.process_financial_query(fi_user_id, query, context_type)
        
        # Save conversation
        save_ai_conversation(session['email'], query, response, context_type)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing AI query: {str(e)}")
        return jsonify({'error': 'Unable to process your query. Please try again.'}), 500

@app.route('/investment-analysis')
def investment_analysis():
    """Get investment analysis"""
    try:
        user = get_user(session['email'])
        fi_user_id = user.get('fi_user_id', '')
        
        if not fi_user_id:
            return jsonify({'error': 'Please connect your Fi account to get investment analysis.'}), 400
        
        analysis = ai_agent.analyze_investment_performance(fi_user_id)
        
        return jsonify({
            'analysis': analysis,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting investment analysis: {str(e)}")
        return jsonify({'error': 'Unable to get investment analysis. Please try again.'}), 500

@app.route('/loan-check', methods=['POST'])
def loan_check():
    """Check loan affordability"""
    try:
        data = request.json
        loan_amount = float(data.get('loan_amount', 0))
        loan_type = data.get('loan_type', 'personal')
        
        user = get_user(session['email'])
        fi_user_id = user.get('fi_user_id', '')
        
        if not fi_user_id:
            return jsonify({'error': 'Please connect your Fi account to check loan eligibility.'}), 400
        
        analysis = ai_agent.check_loan_affordability(fi_user_id, loan_amount, loan_type)
        
        return jsonify({
            'analysis': analysis,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking loan affordability: {str(e)}")
        return jsonify({'error': 'Unable to check loan affordability. Please try again.'}), 500

@app.route('/financial-forecast', methods=['POST'])
def financial_forecast():
    """Get financial forecast"""
    try:
        data = request.json
        target_age = int(data.get('target_age', 60))
        
        user = get_user(session['email'])
        fi_user_id = user.get('fi_user_id', '')
        
        if not fi_user_id:
            return jsonify({'error': 'Please connect your Fi account to get financial forecast.'}), 400
        
        forecast = ai_agent.financial_forecast(fi_user_id, target_age)
        
        return jsonify({
            'forecast': forecast,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating financial forecast: {str(e)}")
        return jsonify({'error': 'Unable to generate financial forecast. Please try again.'}), 500

@app.route('/connect-fi', methods=['POST'])
def connect_fi():
    """Connect Fi account"""
    try:
        data = request.json
        fi_user_id = data.get('fi_user_id', '')
        
        if not fi_user_id:
            return jsonify({'error': 'Fi User ID is required.'}), 400
        
        # Update user's Fi ID
        update_user_fi_id(session['email'], fi_user_id)
        session['fi_user_id'] = fi_user_id
        
        return jsonify({
            'success': True,
            'message': 'Fi account connected successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error connecting Fi account: {str(e)}")
        return jsonify({'error': 'Unable to connect Fi account. Please try again.'}), 500

@app.route('/export-ai-insights')
def export_ai_insights():
    """Export AI insights and conversations"""
    try:
        user = get_user(session['email'])
        conversations = get_user_conversations(session['email'], 100)
        
        # Create CSV export
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Query', 'Response', 'Context Type'])
        
        for conv in conversations:
            writer.writerow([
                conv['timestamp'],
                conv['query'],
                conv['response'][:500] + '...' if len(conv['response']) > 500 else conv['response'],
                conv['context_type']
            ])
        
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'ai_insights_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting AI insights: {str(e)}")
        return jsonify({'error': 'Unable to export insights. Please try again.'}), 500

# Voice Interface Routes
@app.route('/voice-chat')
def voice_chat():
    """Voice chat interface"""
    return render_template('voice_chat.html')

@app.route('/process-voice', methods=['POST'])
def process_voice():
    """Process voice queries"""
    try:
        # This would integrate with speech-to-text and text-to-speech
        # For now, we'll handle text input
        data = request.json
        query = data.get('query', '')
        
        user = get_user(session['email'])
        fi_user_id = user.get('fi_user_id', '')
        
        if not fi_user_id:
            response = "Please connect your Fi account first to get personalized insights."
        else:
            response = ai_agent.process_financial_query(fi_user_id, query, 'voice')
        
        return jsonify({
            'response': response,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing voice query: {str(e)}")
        return jsonify({'error': 'Unable to process voice query. Please try again.'}), 500

# Keep existing routes for backwards compatibility
@app.route('/family_details', methods=['GET', 'POST'])
def family_details():
    if request.method == 'POST':
        family_member_count = int(request.form.get('family_member_count', 0))
        
        for i in range(1, family_member_count + 1):
            name = request.form.get(f'name_{i}')
            age = request.form.get(f'age_{i}')
            income = request.form.get(f'income_{i}')
            relation = request.form.get(f'relation_{i}')
            
            save_family_member(session['email'], name, age, income, relation)
        
        return redirect(url_for('dashboard'))
    
    user = get_user(session['email'])
    family_member_count = int(user['family_members']) - 1
    
    return render_template('family_details.html', count=family_member_count)

def save_family_member(user_email, name, age, income, relation):
    """Save a family member to the database"""
    query = """
    INSERT INTO family_members (user_email, name, age, income, relation)
    VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(query, (user_email, name, age, income, relation))

def get_family_members(user_email):
    """Get all family members for a user"""
    query = """
    SELECT id, name, age, income, relation
    FROM family_members
    WHERE user_email = %s
    """
    return execute_query(query, (user_email,), 'all')

def get_user_by_family_username(family_username):
    query = "SELECT * FROM users WHERE family_username = %s"
    return execute_query(query, (family_username,), 'one')

def has_family_members(email):
    user = get_user(email)
    return int(user['family_members']) > 1

def calculate_age(dob):
    try:
        birth_date = datetime.datetime.strptime(str(dob), '%Y-%m-%d')
        today = datetime.datetime.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        return 0

# Continue with existing routes and add new ones

@app.route('/budget')
def budget_planner():
    user = get_user(session['email'])
    return render_template('budget.html', annual_income=float(user['annual_income']))

@app.route('/generate-budget')
def generate_budget():
    user = get_user(session['email'])
    income = float(user['annual_income'])
    
    plan = {
        'name': 'AI-Optimized Budget Plan',
        'allocations': {
            'Essentials': {
                'Food & Groceries': income * 0.15,
                'Rent/EMI': income * 0.25,
                'Utilities': income * 0.05,
                'Transportation': income * 0.08
            },
            'Lifestyle': {
                'Entertainment': income * 0.07,
                'Dining Out': income * 0.05,
                'Subscriptions': income * 0.03,
                'Shopping': income * 0.04
            },
            'Savings & Investments': {
                'Emergency Fund': income * 0.10,
                'Mutual Funds': income * 0.07,
                'FD/RD': income * 0.05
            },
            'Miscellaneous': {
                'Healthcare': income * 0.03,
                'Insurance': income * 0.02,
                'Gifts': income * 0.01
            }
        }
    }
    return jsonify({'plans': [plan]})

@app.route('/save-budget', methods=['POST'])
def save_budget():
    try:
        email = session['email']
        data = request.get_json()
        budgets = data.get('budgets', [])

        if not budgets:
            return jsonify({"success": False, "message": "No budget data received."}), 400

        # Delete existing budget for the user
        delete_query = "DELETE FROM budgets WHERE email = %s"
        execute_query(delete_query, (email,))

        # Insert new budget items
        insert_query = """
        INSERT INTO budgets (email, main_category, sub_category, amount, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
        """

        for item in budgets:
            execute_query(insert_query, (
                email,
                item['mainCategory'],
                item['subCategory'],
                item['amount']
            ))

        return jsonify({"success": True, "message": "Budget saved successfully."})

    except Exception as e:
        logger.error(f"Error saving budget: {str(e)}")
        return jsonify({"success": False, "message": "Failed to save budget."}), 500


@app.route('/expense')
def expense():
    return render_template('expense.html')

@app.route('/schemes')
def schemes():
    schemes_data = [
        {"Name": "Pradhan Mantri Awas Yojana", "Eligibility": "Income < 180000, Family size >= 2", "Description": "Housing subsidy scheme to provide affordable housing for economically weaker sections.", "Documents": "Aadhaar, Income Proof, Residence Proof, Family Details", "Process": "1. Visit the official PMAY website or local municipal office.\n2. Fill out the application form with details.\n3. Submit required documents online or offline.\n4. Authorities will review the application.\n5. If approved, subsidy will be credited to the bank account."},
        {"Name": "Pradhan Mantri Jan Dhan Yojana", "Eligibility": "Any Indian citizen, No existing bank account", "Description": "Financial inclusion scheme providing zero-balance bank accounts with insurance benefits.", "Documents": "Aadhaar, Voter ID, Passport-size Photo", "Process": "1. Visit a bank or Business Correspondent (Bank Mitra).\n2. Fill out the application form for a Jan Dhan account.\n3. Submit identity and address proof documents.\n4. Bank verifies the details and opens the account.\n5. Account holder receives a RuPay debit card with insurance benefits."},
        {"Name": "Atal Pension Yojana", "Eligibility": "Age 18-40, Must have a savings bank account", "Description": "Retirement pension scheme for unorganized sector workers.", "Documents": "Aadhaar, Bank Account Details, Mobile Number", "Process": "1. Visit your bank or post office offering the scheme.\n2. Fill out the APY application form and select pension amount.\n3. Link Aadhaar and provide bank details.\n4. Set up auto-debit for monthly contributions.\n5. Pension starts after reaching the eligible retirement age."},
        {"Name": "Pradhan Mantri Kisan Samman Nidhi", "Eligibility": "Small & marginal farmers with landholding up to 2 hectares", "Description": "Income support scheme providing ₹6,000 per year to farmers.", "Documents": "Aadhaar, Land Ownership Document, Bank Account Details", "Process": "1. Register through the PM-KISAN portal or local agriculture office.\n2. Submit Aadhaar, land ownership proof, and bank details.\n3. Government verifies eligibility and processes application.\n4. Approved farmers receive ₹6,000 annually in three installments."},
        {"Name": "Ayushman Bharat Yojana", "Eligibility": "Low-income families, No existing health insurance", "Description": "Health insurance scheme providing free treatment up to ₹5 lakh.", "Documents": "Aadhaar, Income Certificate, Ration Card", "Process": "1. Check eligibility on the Ayushman Bharat website.\n2. Visit an empaneled hospital or CSC center.\n3. Provide Aadhaar and income proof for verification.\n4. If eligible, receive an Ayushman card.\n5. Get free treatment at listed hospitals."}
    ]
    return render_template('schemes.html', schemes=schemes_data)
def find_matching_schemes(user):
    """
    Matches user with schemes from 'government_schemes' table based on simple rule extraction.
    user = {
        "age": 30,
        "income": 250000,
        "gender": "Female",
        "profession": "Farmer"
    }
    """
    query = "SELECT id, name, eligibility, target_group, income_limit FROM government_schemes"
    all_schemes = execute_query(query, fetch='all')  # Assumes your DB fetch helper

    matching_schemes = []

    for scheme in all_schemes:
        eligible = True

        # Income check
        if scheme['income_limit'] and user.get('income'):
            if user['income'] > scheme['income_limit']:
                eligible = False

        # Gender-based check
        if scheme['target_group'] and user.get('gender'):
            if scheme['target_group'].lower() == "women" and user['gender'].lower() != "female":
                eligible = False
            elif scheme['target_group'].lower() == "men" and user['gender'].lower() != "male":
                eligible = False

        # Simple keyword matching in 'eligibility' text (can expand with NLP later)
        if scheme['eligibility']:
            eligibility_text = scheme['eligibility'].lower()
            if "farmer" in eligibility_text and "farmer" not in user.get('profession', '').lower():
                eligible = False
            if "entrepreneur" in eligibility_text and "entrepreneur" not in user.get('profession', '').lower():
                eligible = False
            if "disabled" in eligibility_text and user.get('disability') != True:
                eligible = False

        if eligible:
            matching_schemes.append({
                "id": scheme['id'],
                "name": scheme['name'],
                "eligibility": scheme['eligibility']
            })

    return matching_schemes


# GET: Serve the match schemes form
@app.route('/match-schemes', methods=['GET'])
def match_schemes_page():
    return render_template('match_schemes.html')

# POST: Receive user info, return matched schemes
@app.route('/match-schemes/api', methods=['POST'])
def match_schemes_api():
    try:
        data = request.get_json()
        user = {
            "age": data['age'],
            "gender": data['gender'],
            "income": data['income'],
            "profession": data['profession']
        }

        matched = find_matching_schemes(user)  # Your logic function
        return jsonify(matched)

    except Exception as e:
        logger.error(f"Error matching schemes: {str(e)}")
        return jsonify([]), 500


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user = get_user(session['email'])
    fi_user_id = user.get('fi_user_id', '')
    
    # Use AI agent if Fi account is connected
    if fi_user_id:
        response = ai_agent.process_financial_query(fi_user_id, data['message'], 'chat')
        save_ai_conversation(session['email'], data['message'], response, 'chat')
    else:
        # Fallback to basic chatbot
        try:
            response = client.generate_content(data['message'])
            response = response.text
        except Exception as e:
            response = f"Error: {str(e)}"
    
    return jsonify({'response': response})

@app.route('/save-expense', methods=['POST'])
def save_expense():
    expense_data = request.json
    main_category = expense_data['mainCategory']
    sub_category = expense_data['subCategory']
    amount = expense_data['amount']
    email = session['email']
    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    execute_query(
        "INSERT INTO expenses (email, main_category, sub_category, amount, date) VALUES (%s, %s, %s, %s, %s)",
        (email, main_category, sub_category, amount, date)
    )

    return jsonify({'status': 'success'})

@app.route('/view-expenses')
def view_expenses():
    email = session['email']
    
    query = "SELECT main_category, sub_category, amount, date FROM expenses WHERE email = %s"
    expenses = execute_query(query, (email,), 'all')
    
    return render_template('view_expenses.html', expenses=expenses)

@app.route('/family-expense')
def family_expense():
    try:
        user = get_user(session['email'])
        
        # Get family members
        family_members = get_family_members(user['email'])
        
        # Get family expenses (you might want to create a separate table for family expenses)
        family_expenses = get_family_expenses(user['email'])
        
        return render_template('family_expense.html', 
                             family_members=family_members, 
                             expenses=family_expenses)
        
    except Exception as e:
        logger.error(f"Error loading family expense page: {str(e)}")
        return render_template('family_expense.html', 
                             family_members=[], 
                             expenses=[], 
                             error="Unable to load family expense data")

def get_family_expenses(user_email):
    """Get family expenses - you might need to modify this based on your table structure"""
    try:
        # Option 1: If you have a separate family_expenses table
        query = """
        SELECT fe.id, fe.member_name, fe.main_category, fe.sub_category, 
               fe.amount, fe.date, fm.relation
        FROM family_expenses fe
        LEFT JOIN family_members fm ON fe.member_name = fm.name
        WHERE fe.user_email = %s
        ORDER BY fe.date DESC
        """
        
        # Option 2: If you're using the same expenses table with member identification
        # query = """
        # SELECT e.id, e.main_category, e.sub_category, e.amount, e.date,
        #        COALESCE(e.member_name, 'Self') as member_name
        # FROM expenses e
        # WHERE e.email = %s
        # ORDER BY e.date DESC
        # """
        
        return execute_query(query, (user_email,), 'all') or []
        
    except Exception as e:
        logger.error(f"Error fetching family expenses: {str(e)}")
        return []

def save_family_expense(user_email, member_name, main_category, sub_category, amount, date=None):
    """Save a family expense"""
    try:
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Option 1: Save to family_expenses table
        query = """
        INSERT INTO family_expenses (user_email, member_name, main_category, sub_category, amount, date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Option 2: Save to expenses table with member identification
        # query = """
        # INSERT INTO expenses (email, main_category, sub_category, amount, date, member_name)
        # VALUES (%s, %s, %s, %s, %s, %s)
        # """
        
        execute_query(query, (user_email, member_name, main_category, sub_category, amount, date))
        return True
        
    except Exception as e:
        logger.error(f"Error saving family expense: {str(e)}")
        return False

@app.route('/save_family_expense', methods=['POST'])
def add_family_expense():
    try:
        data = request.get_json()
        email = session['email']
        
        success = save_family_expense(
            email,
            data['memberName'],
            data['mainCategory'],
            data['subCategory'],
            data['amount'],
            data.get('date')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Family expense added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add family expense'}), 500
            
    except Exception as e:
        logger.error(f"Error adding family expense: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
@app.route('/view-family-expenses')
def view_family_expenses():
    try:
        user = get_user(session['email'])
        expenses = get_family_expenses(user['email'])
        return render_template('view_family_expenses.html', expenses=expenses)
    except Exception as e:
        logger.error(f"Error loading family expense view: {str(e)}")
        return render_template('view_family_expenses.html', expenses=[], error="Unable to load data")


@app.route('/add-expense', methods=['POST'])
def add_expense():
    data = request.get_json()
    email = session['email']
    
    execute_query(
        "INSERT INTO expenses (email, main_category, sub_category, amount, date) VALUES (%s, %s, %s, %s, %s)",
        (email, data['mainCategory'], data['subCategory'], data['amount'], data['date'])
    )
    
    return jsonify({'success': True})

@app.route('/get-expenses', methods=['GET'])
def get_expenses():
    email = session['email']
    print("Fetching expenses for:", email) 
    
    expenses = execute_query(
        "SELECT id, main_category as mainCategory, sub_category as subCategory, amount, date FROM expenses WHERE email = %s",
        (email,), 'all'
    )
    
    budgets = execute_query(
        "SELECT main_category as mainCategory, sub_category as subCategory, amount FROM budgets WHERE email = %s",
        (email,), 'all'
    )
    
    if not budgets:
        budgets = [
            {"mainCategory": "Essentials", "subCategory": "Food & Groceries", "amount": 5000}, 
            {"mainCategory": "Lifestyle", "subCategory": "Entertainment", "amount": 2000}, 
            {"mainCategory": "Savings", "subCategory": "Emergency Fund", "amount": 3000},
            {"mainCategory": "Miscellaneous", "subCategory": "Healthcare", "amount": 1000}
        ]
    print("Expenses returned:", expenses)
    return jsonify({"expenses": expenses, "budget": budgets})

@app.route('/delete-expense/<int:id>', methods=['DELETE'])
def delete_expense(id):
    email = session['email']
    
    execute_query(
        "DELETE FROM expenses WHERE id = %s AND email = %s",
        (id, email)
    )
    
    return jsonify({'success': True})

@app.route('/export-expenses', methods=['GET'])
def export_expenses():
    email = session['email']
    
    expenses = execute_query(
        "SELECT main_category, sub_category, amount, date FROM expenses WHERE email = %s",
        (email,), 'all'
    )
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Main Category', 'Subcategory', 'Amount (INR)', 'Date'])
    
    for exp in expenses:
        writer.writerow([exp['main_category'], exp['sub_category'], exp['amount'], exp['date']])
    
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='expenses.csv')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API Routes for External Integration
@app.route('/api/financial-profile', methods=['GET'])
def api_financial_profile():
    """API endpoint to get financial profile"""
    try:
        user = get_user(session['email'])
        fi_user_id = user.get('fi_user_id', '')
        
        if not fi_user_id:
            return jsonify({'error': 'Fi account not connected'}), 400
        
        profile = fi_mcp_client.get_financial_profile(fi_user_id)
        
        if not profile:
            return jsonify({'error': 'Unable to fetch financial profile'}), 500
        
        return jsonify({
            'profile': {
                'net_worth': profile.net_worth,
                'total_assets': profile.total_assets,
                'total_liabilities': profile.total_liabilities,
                'credit_score': profile.credit_score,
                'monthly_income': profile.monthly_income,
                'monthly_expenses': profile.monthly_expenses,
                'epf_balance': profile.epf_balance,
                'last_updated': profile.last_updated.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching financial profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ai-insights', methods=['POST'])
def api_ai_insights():
    """API endpoint for AI insights"""
    try:
        data = request.json
        query = data.get('query', '')
        
        user = get_user(session['email'])
        fi_user_id = user.get('fi_user_id', '')
        
        if not fi_user_id:
            return jsonify({'error': 'Fi account not connected'}), 400
        
        response = ai_agent.process_financial_query(fi_user_id, query, 'api')
        
        return jsonify({
            'response': response,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing AI insights: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    

#error handling
# Add this error handler to your Flask app
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

# Improved database connection with retry logic
def get_db_connection_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            return db_pool.get_connection()
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)

def execute_query_safe(query, params=None, fetch=None):
    """Execute SQL query with better error handling"""
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection_with_retry()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(query, params or ())
        
        if fetch == 'one':
            result = cursor.fetchone()
        elif fetch == 'all':
            result = cursor.fetchall()
        else:
            connection.commit()
            result = None
            
        return result
        
    except mysql.connector.Error as e:
        logger.error(f"Database error: {str(e)}")
        if connection:
            connection.rollback()
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in execute_query: {str(e)}")
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Replace your existing execute_query function with execute_query_safe

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)