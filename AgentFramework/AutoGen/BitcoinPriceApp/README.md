# 实时比特币价格显示应用

这是一个基于 Streamlit 构建的轻量级 Web 应用，用于实时显示比特币（BTC）的当前美元价格及其过去24小时的涨跌幅和涨跌额。

## 核心功能

*   **实时价格显示**：获取并显示比特币当前的美元价格。
*   **24小时价格变化**：显示比特币在过去24小时内的价格涨跌幅（百分比）和涨跌额（美元）。
*   **价格刷新**：提供一个按钮，允许用户手动刷新价格数据。
*   **趋势可视化**：价格上涨时显示绿色，下跌时显示红色。
*   **错误处理与加载状态**：在数据获取过程中显示加载动画，并在遇到问题时提供友好的错误提示。

## 技术栈

*   **前端框架**：Streamlit
*   **编程语言**：Python
*   **数据源**：CoinGecko Public API (v3)
*   **Python 库**：`requests` (用于API调用), `streamlit`

## 如何运行

1.  **克隆或下载项目**：
    ```bash
    git clone <repository_url>
    cd <repository_folder>/AgentFramework/AutoGen/BitcoinPriceApp
    ```
    (如果您是直接下载，请确保进入 `BitcoinPriceApp` 目录)

2.  **创建并激活虚拟环境 (推荐)**：
    ```bash
    python -m venv venv
    # Windows
    .\\venv\\Scripts\\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```
    **注意**: 这里没有 `requirements.txt` 文件。请手动创建 `requirements.txt` 并添加以下内容：
    ```
    streamlit
    requests
    ```
    然后再次运行 `pip install -r requirements.txt`。

4.  **运行 Streamlit 应用**：
    ```bash
    streamlit run app.py
    ```

    应用将在您的默认浏览器中打开 (通常是 `http://localhost:8501`)。

## 界面预览

-   **应用启动**：
    当应用首次启动或刷新时，会显示一个加载指示器，直到数据获取完成。

-   **正常显示**：
    一旦数据加载成功，界面将显示比特币的当前价格、24小时百分比变化和绝对金额变化。涨跌趋势会以绿色（上涨）或红色（下跌）显示。

-   **刷新功能**：
    点击“🔄 刷新价格”按钮，将清除缓存并重新从 CoinGecko API 获取最新数据。

-   **错误处理**：
    如果API调用失败（例如，网络问题、API服务中断或数据结构不符），界面会显示友好的错误信息，而不是崩溃。

## API 数据源

本应用使用 [CoinGecko Public API (v3)](<https://www.coingecko.com/api/documentation>) 获取比特币价格数据。该API免费且无需认证即可访问基本价格信息。

## 开发者注意事项

*   **数据精度**：为确保金融计算的精确性，应用内部使用 Python 的 `decimal` 模块进行价格和变化的计算。
*   **API 限流**：CoinGecko Public API 对免费用户有请求限制（通常是每分钟50-100次请求）。应用中的 `st.cache_data(ttl=60)` 机制会在本地缓存数据60秒，有效减少对API的请求频率，避免触发限流。
*   **错误处理**：代码中包含了对网络错误、HTTP错误、JSON解析错误和数据结构错误的捕获和处理，以提高应用的健壮性。

