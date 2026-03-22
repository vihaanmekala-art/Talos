"""
Project: Talos v1.0.1
Description: Multi-functional AI & Financial Analysis Hub.
License: Proprietary / All Rights Reserved.
Copyright (c) [Vihaan Mekala] All rights reserved.
This software is proprietary. Resale or redistribution is strictly prohibited.

"""

import streamlit as st
import random
import streamlit_authenticator as stauth
from streamlit_util import calculate
from streamlit_util import stocks
from streamlit_util import stock_analysis
from streamlit_util import pull_data
from streamlit_util import initialize_db
from streamlit_util import create_sql
from streamlit_util import port
from streamlit_util import intr
from streamlit_util import show_macro
from streamlit.runtime.scriptrunner import RerunException
from streamlit.runtime.scriptrunner import get_script_run_ctx

initialize_db()
st.session_state['analysis'] = False
main_area = st.container()


credentials = pull_data()   
cookie_key = st.secrets['COOKIE_SECRET_KEY']

authenticator = stauth.Authenticate(
    credentials,
    "talos_cookie",      
    cookie_key,     
    cookie_expiry_days=30
)


if 'registering' not in st.session_state:
    st.session_state['registering'] = False

if "register_render_count" not in st.session_state:
    st.session_state["register_render_count"] = 0

if 'stock' not in st.session_state:
    st.session_state['stock'] = False

if not st.session_state.get("registering"):
    try:
        
        authenticator.login(location="main")
    except Exception as e:
        pass
authentication_status = st.session_state.get("authentication_status")

if authentication_status is None and not st.session_state.get('registering'):
    
    if st.button("Register"):
        st.session_state["registering"] = True
        st.rerun()

if st.session_state.get('registering'):
    st.subheader('Register')
    try:
        
        registered = authenticator.register_user(location='main', key='register_user_form')
        st.session_state['register_render_count'] += 1
    
        
        if registered and st.session_state['register_render_count'] > 1:
            reg_email, reg_username, reg_name = registered
            
            hashed_password = credentials['usernames'][reg_username]['password']
            
            try:
                conn = create_sql()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, name, email, password_hash)
                    VALUES (?, ?, ?, ?)
                ''', (reg_username, reg_name, reg_email, hashed_password))
                conn.commit()
                conn.close()
                st.success('The registration is now complete! You can use these credentials now. In order to use them, just refresh the tab!')
                
                st.session_state['register_render_count'] = 0

                st.session_state['registering'] = False

                raise RerunException(get_script_run_ctx())
            except Exception as e:
                st.error(f'{e}')
            
            

            
            

    except Exception as e:
        st.error(f'Something went wrong...{e}')    





if authentication_status:




    with main_area:
        name = st.session_state.get('name','user')
        if st.session_state.get('username') == 'demo_123':
            pass
        st.sidebar.write(f'Welcome back, {name}')
        authenticator.logout(button_name='Logout', location='sidebar')
        
        options = [
                "🏠 Home Page",
                "🧠 Calculate an Expression",
                "📈 Stock Analysis",
                "⚖️ Portfolio Optimizer",
                '📊 Intrinsic Value',
                '🌐 Macro Information',
                '📊 Options Chain'
            ]
        

        
        st.sidebar.title("Talos v.1.1.0")
        st.title("Talos v.1.1.0")
        option = st.sidebar.radio(
            "Options",
            options=options,
            label_visibility='collapsed'
        )

        if 'current_option' not in st.session_state:
            st.session_state['current_option'] = option

        if st.session_state['current_option'] != option:
            st.session_state['current_option'] = option
            st.rerun()
        theme = st.sidebar.radio('Select a Theme',['Light','Dark [Beta]'])
        if theme == 'Light':
            st.markdown("""
                <style>
                .stApp {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                [data-testid="stSidebar"] {
                    background-color: #F0F2F6;
                }
                </style>
                """, unsafe_allow_html=True)
        else:
            st.sidebar.caption('Some elements may not be seen.')
            st.markdown("""
            <style>
            .stApp {
                background-color: #0E1117;
            }

            .stApp, .stMarkdown, .stText, .stMetric, .stSubheader, 
            .stHeader, .stCaption, p, div, span, label {
                color: #FFFFFF !important;
            }

            [data-testid="stSidebar"] {
                background-color: #262730;
            }

            /* Fix metrics */
            [data-testid="stMetricValue"] {
                color: #FFFFFF !important;
            }

            /* Fix input fields */
            input, textarea {
                color: #FFFFFF !important;
                background-color: #262730 !important;
            }
            </style>
            """, unsafe_allow_html=True)


        st.divider()
        if option != '📈 Stock Analysis':
            st.session_state['stock'] = False
        if option == '🏠 Home Page':
            col2,col3 = st.columns(2)
            with col2:
                st.subheader('AI insights.')
                tips = [
            "Use 'Golden Cross' signals for long-term stock trends.",
            "Always check the RSI before buying a big price jump.",
            "Keep your RAM usage below 80% for the best coding speed.",
            "Python's 'Pandas' library is named after 'Panel Data'!"
        ] 
                
            random.shuffle(tips)
            st.write(tips[-1])
            if st.button('Generate a Fact'):
                st.write(tips[-1])

        elif option == "🧠 Calculate an Expression":
            st.write("This was made possible with the Sympy Library.")
            st.write("Format trig ratios as Sin(30) or Cos(85)")
            question = st.text_input("Ask a math question: ")

            answer = calculate(question)

            st.success(answer)
        elif option == "📈 Stock Analysis":
            
            
            file = st.file_uploader('Choose a JSON or CSV file.', type = ['json', 'csv'])
            if file is not None:
                stock_analysis(file)
            else:
                st.info('Or you can use the built-in stock analysis function!')
                if st.button('Type stock ticker'):
                    st.session_state['stock'] = True
                
                if st.session_state.get('stock', False):
                    stocks()
        elif option == '⚖️ Portfolio Optimizer':
            
            tickers = st.text_input('Choose 2 stocks. Format as AAPL, NVDA.')
            tickers = [t.strip().upper() for t in tickers.split(',')]
            if st.button('Optimize'):
                with st.spinner('HELP'):
                    
                    fig, max_sharpe_df, min_vol, tickers = port(tickers)

                    col1a, col2a = st.columns(2)
                    with col1a:
                        st.subheader('⭐ Max Sharpe Portfolio')
                        st.metric('Expected Return', f"{max_sharpe_df['returns']:.2%}")
                        st.metric('Expected Risk', f"{max_sharpe_df['risk']:.2%}")
                        st.metric('Sharpe Ratio', f"{max_sharpe_df['sharpe']:.2f}")
                        st.write('**Allocations:**')
                        for ticker, w in zip(tickers, max_sharpe_df['Weight']):
                            st.write(f"- {ticker}: {w:.1%}")
                    with col2a:
                        st.subheader('🛡️ Min Volatility Portfolio')
                        st.metric('Expected Return', f"{min_vol['returns']:.2%}")
                        st.metric('Expected Risk', f"{min_vol['risk']:.2%}")
                        st.metric('Sharpe Ratio', f"{min_vol['sharpe']:.2f}")
                        st.write('**Allocations:**')
                        for ticker, w in zip(tickers, min_vol['Weight']):
                            st.write(f"- {ticker}: {w:.1%}")

                    st.plotly_chart(fig)
                    st.warning('For educational purposes only. Not financial advice.')
        elif option == '📊 Intrinsic Value': 
            ticker = st.text_input('Type in your stock ticker.')
            col1, col2, col3 = st.columns(3)

            with col1:
                growth_rate = st.slider(
                    'FCF Growth Rate (%)',
                    min_value=0,
                    max_value=50,
                    value=8, 
                    step=1
                ) / 100 

            with col2:
                discount_rate = st.slider(
                    'Discount Rate (%)',
                    min_value=1,
                    max_value=20,
                    value=10,
                    step=1
                ) / 100

            with col3:
                terminal_growth = st.slider(
                    'Terminal Growth Rate (%)',
                    min_value=0,
                    max_value=10,
                    value=3,
                    step=1
                ) / 100
            if st.button('Calculate'):
                if ticker:
                    result = intr(ticker, growth_rate, discount_rate, terminal_growth)
                if result:
                    intrinsic_value_per_share, current_price, df_proj, terminal_value_pv = result
                    st.metric('Current Price', value=current_price)
                    st.metric('Intrinsic Value', value=intrinsic_value_per_share)
                    st.metric('Terminal Value', value=f'{terminal_value_pv:.2f}B')
                    st.dataframe(df_proj)
                    if intrinsic_value_per_share > current_price * 1.15:
                            verdict = '🟢 Undervalued'
                    elif intrinsic_value_per_share < current_price * 0.85:
                        verdict = '🔴 Overvalued'
                    else:
                        verdict = '🟡 Fairly Valued'
                
                st.subheader(verdict)
                    
                st.warning('For educational purposes only. Not financial advice.')
        elif option == '🌐 Macro Information':
            with st.spinner('Crunching Data...'):
                show_macro()
        
        elif option == '📊 Options Chain':
            import yfinance as yf   
            stock = st.text_input('Choose a Stock. Format as NVDA.')
            if stock:
                ticker = yf.Ticker(stock)
                price = yf.download(stock)
                expirations = ticker.options
                choice = st.selectbox('Choose an Expiry Date', options=expirations)
                st.metric('Current Price', value=f'${price}')
                chain = stock.option_chain(choice)
                calls = chain.calls
                puts = chain.puts
                important_cols = ['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
                st.subheader('📈 Call Options')
                st.dataframe(calls[important_cols])
                st.subheader('📉 Put Options')
                st.dataframe(puts[important_cols])
elif authentication_status is False:
    st.error('Incorrect username/password')
    if st.button('Forgot My Password'):
        try:
            temp_username, temp_email, temp_password = authenticator.forgot_password(location='main')
            if temp_password:
                st.success(f'New password was generated for {temp_username}')
                st.success(f'The password is {temp_password}')
            elif not temp_password:
                st.error('Username not found...')
        except Exception as e:
            st.error(f'Something went wrong...{e}') 
elif authentication_status is None:
    st.warning('Please provide a username/password.')