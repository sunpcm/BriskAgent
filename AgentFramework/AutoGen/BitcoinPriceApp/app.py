import streamlit as st
import requests
import json
import decimal

# 设置页面配置，包括标题和图标
st.set_page_config(
    page_title="实时比特币价格",
    page_icon="₿",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- 配置 ---
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
CURRENCY_PAIR = "bitcoin"
VS_CURRENCIES = "usd"

# 使用Decimal模块进行精确计算，避免浮点数精度问题
decimal.getcontext().prec = 10 # 设置精度

# --- 数据获取模块 ---
@st.cache_data(ttl=60) # 缓存数据60秒，避免频繁API调用
def fetch_bitcoin_price():
    """
    从CoinGecko API获取比特币当前价格和24小时变化。
    """
    params = {
        "ids": CURRENCY_PAIR,
        "vs_currencies": VS_CURRENCIES,
        "include_24hr_change": "true"
    }
    try:
        response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
        response.raise_for_status() # 如果状态码不是200，则抛出HTTPError

        data = response.json()

        # 检查API返回数据结构是否符合预期
        if CURRENCY_PAIR not in data or VS_CURRENCIES not in data[CURRENCY_PAIR]:
            st.error("API返回数据结构不符合预期。请稍后再试。")
            st.json(data) # 打印原始数据方便调试
            return None

        print(data)

        return data

    except requests.exceptions.Timeout:
        st.error("网络请求超时，请检查您的网络连接或稍后再试。")
        return None
    except requests.exceptions.ConnectionError:
        st.error("无法连接到API服务。请检查您的网络连接。")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API请求失败，状态码: {e.response.status_code}. 错误信息: {e.response.text}")
        return None
    except json.JSONDecodeError:
        st.error("API返回了无效的JSON格式数据。")
        return None
    except Exception as e:
        st.error(f"发生未知错误: {e}")
        return None

# --- 数据处理模块 ---
def process_price_data(raw_data):
    """
    处理原始API数据，提取并格式化比特币价格和24小时变化。
    返回格式化的字典或None。
    """
    if not raw_data:
        return None

    try:
        btc_data = raw_data[CURRENCY_PAIR]
        current_price = decimal.Decimal(str(btc_data[VS_CURRENCIES]))
        # CoinGecko直接提供了24小时百分比变化
        change_24hr_percent = decimal.Decimal(str(btc_data[f"{VS_CURRENCIES}_24h_change"]))

        # 计算24小时涨跌额
        # 公式：当前价格 / (1 + 24小时百分比变化/100) = 24小时前价格
        # 涨跌额 = 当前价格 - 24小时前价格
        # 避免除以零或非常小的数
        if (1 + change_24hr_percent / 100) == 0:
            previous_price = current_price # Fallback to current if percentage makes divisor zero
        else:
            previous_price = current_price / (1 + (change_24hr_percent / 100))

        change_24hr_amount = current_price - previous_price

        return {
            "current_price": current_price,
            "change_24hr_percent": change_24hr_percent,
            "change_24hr_amount": change_24hr_amount
        }
    except KeyError as e:
        st.error(f"处理数据时发现缺少键: {e}。API返回数据结构可能已改变。")
        return None
    except (ValueError, decimal.InvalidOperation) as e:
        st.error(f"处理数据时发生数值转换错误: {e}。API返回了非数字格式。")
        return None
    except Exception as e:
        st.error(f"处理数据时发生未知错误: {e}")
        return None

# --- 用户界面模块 (Streamlit) ---
def display_bitcoin_price(data):
    """
    在Streamlit界面上显示比特币价格信息。
    """
    st.title("₿ 实时比特币价格 (USD)")

    # 刷新按钮
    if st.button("🔄 刷新价格"):
        st.cache_data.clear() # 清除缓存，强制重新获取数据
        st.rerun() # 重新运行应用，触发数据获取

    if data:
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="当前价格",
                value=f"${data['current_price']:,.2f}",
                help="比特币当前美元价格"
            )

        with col2:
            # 根据涨跌幅设置颜色和前缀
            delta_color = "normal"
            if data['change_24hr_percent'] > 0:
                delta_color = "inverse" # Streamlit metric delta_color="inverse" makes positive green
            elif data['change_24hr_percent'] < 0:
                delta_color = "off" # Streamlit metric delta_color="off" makes negative red

            # 格式化涨跌幅
            percent_str = f"{data['change_24hr_percent']:+.2f}%"
            # 格式化涨跌额
            amount_str = f"${data['change_24hr_amount']:+.2f}"

            st.metric(
                label="24小时变化",
                value=percent_str,
                delta=amount_str, # delta字段会自动根据正负值显示颜色和箭头
                delta_color=delta_color, # 'normal' (black), 'inverse' (green), 'off' (red)
                help="过去24小时的价格变化（百分比和金额）"
            )
        st.info("数据每60秒自动刷新，或点击刷新按钮手动刷新。")
    else:
        st.warning("未能获取或处理比特币价格数据。请检查上述错误信息。")

# --- 应用主逻辑模块 ---
def main():
    with st.spinner("正在获取比特币价格数据..."):
        raw_data = fetch_bitcoin_price()

    processed_data = process_price_data(raw_data)
    display_bitcoin_price(processed_data)

if __name__ == "__main__":
    main()

