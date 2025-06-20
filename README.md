# DeepX - 多接口集成的子域名收集工具

DeepX是一个多接口集成的子域名收集工具，专注于发现隐藏子域名资产。通过集成多个接口并分析比较结果，可以找出不同来源之间的差异，发现可能被遗漏的子域名。

## 特性

- **多接口集成**：集成OTX、Crt.sh、Archive.org等多个数据源
- **FOFA查询**：使用FOFA API进行子域名查询
- **字典爆破**：支持字典爆破子域名
- **隐藏资产发现**：通过比较不同来源的结果，找出隐藏的子域名资产
- **测活检测**：检测子域名是否存活，支持HTTP和HTTPS协议
- **异步处理**：采用异步技术加速处理速度
- **缓存机制**：支持结果缓存，避免重复查询
- **模块化设计**：便于扩展和维护

## 安装

确保已安装Python 3.7或更高版本，然后安装依赖：

```bash
pip install -r requirements.txt
```

## 配置

1. FOFA API配置：

   创建`config/secrets.py`文件，添加FOFA API密钥：

   ```python
   FOFA_API_KEY = "your_fofa_api_key"
   ```

   或者在环境变量中设置：

   ```bash
   export FOFA_API_KEY="your_fofa_api_key"
   ```

2. 其他配置项请参考`config/config.py`。

## 使用方法

### 基本用法

```bash
# 使用传统方法收集子域名
python DeepX.py collect example.com

# 使用FOFA API收集子域名
python DeepX.py fofa example.com

# 比较不同来源的域名结果，找出隐藏域名
python DeepX.py compare example.com

# 对域名进行存活性检测
python DeepX.py alive example.com

# 执行完整流程（收集、FOFA、比较和测活）
python DeepX.py all example.com
```

### 高级选项

```bash
# 禁用缓存
python DeepX.py all example.com --no-cache

# 启用字典爆破
python DeepX.py all example.com --enable-brute

# 指定FOFA API密钥
python DeepX.py fofa example.com --key "your_fofa_api_key"

# 禁用测活
python DeepX.py all example.com --no-alive

# 单独执行测活检测
python DeepX.py alive example.com --input-file domains.txt

# 比较并测活
python DeepX.py compare example.com --alive
```

## 命令详解

### collect - 使用传统方法收集子域名

```
python DeepX.py collect example.com [options]
```

选项：
- `-d, --debug`：启用调试输出（默认已启用）
- `--no-debug`：禁用调试输出
- `-o, --output`：输出文件名
- `--collectors`：指定要使用的收集器（可选：otx, crt, archive）
- `--no-cache`：禁用域名缓存
- `--cache-days`：缓存有效期（天）
- `--no-brute`：禁用字典爆破

### fofa - 使用FOFA API收集子域名

```
python DeepX.py fofa example.com [options]
```

选项：
- `-d, --debug`：启用调试输出（默认已启用）
- `--no-debug`：禁用调试输出
- `-o, --output`：输出文件名
- `--key`：FOFA API密钥（优先于配置文件）

### compare - 比较不同来源的域名结果

```
python DeepX.py compare example.com [options]
```

选项：
- `-d, --debug`：启用调试输出（默认已启用）
- `--deep-file`：DeepX结果文件
- `--fofa-file`：FOFA结果文件
- `--brute-file`：爆破结果文件
- `-r, --result`：隐藏域名结果文件
- `-t, --total`：总资产域名结果文件
- `--alive`：启用测活（检查域名是否存活）
- `--no-cache`：禁用域名缓存

### alive - 测试域名是否存活

```
python DeepX.py alive example.com [options]
```

选项：
- `-d, --debug`：启用调试输出（默认已启用）
- `--no-debug`：禁用调试输出
- `--input-file`：输入文件，包含要测活的域名列表（每行一个域名）
- `--hidden-file`：隐藏域名结果文件
- `--normal-file`：普通域名结果文件
- `--no-cache`：禁用域名缓存

### brute - 使用字典爆破子域名

```
python DeepX.py brute example.com [options]
```

选项：
- `-d, --debug`：启用调试输出（默认已启用）
- `--no-debug`：禁用调试输出
- `-o, --output`：输出文件名

### all - 执行完整流程

```
python DeepX.py all example.com [options]
```

选项：
- `-d, --debug`：启用调试输出（默认已启用）
- `--no-debug`：禁用调试输出
- `--key`：FOFA API密钥（优先于配置文件）
- `--no-cache`：禁用域名缓存
- `--cache-days`：缓存有效期（天）
- `--enable-brute`：启用字典爆破（默认禁用）
- `--no-alive`：禁用测活（默认启用）

## 输出文件

所有输出文件默认保存在`output`目录下，文件命名格式为`文件分类_目标域名_时间戳.txt`，例如：

- `deep_example.com_20250620_120000.txt`：深度收集的子域名
- `fofa_example.com_20250620_120000.txt`：FOFA收集的子域名
- `hidden_example.com_20250620_120000.txt`：隐藏的子域名（在深度收集中但不在FOFA中）
- `brute_example.com_20250620_120000.txt`：爆破得到的子域名
- `total_example.com_20250620_120000.txt`：所有来源的子域名合集
- `alive_hidden_example.com_20250620_120000.txt`：隐藏域名的存活检测结果
- `alive_normal_example.com_20250620_120000.txt`：普通域名的存活检测结果
- `alive_all_example.com_20250620_120000.txt`：所有域名的存活检测结果

## 测活结果输出格式

存活域名输出格式：
```
https://example.com [状态码: 200] [标题: Example Domain] [大小: 1234 字节]
```

不存活域名输出格式：
```
https://subdomain.example.com [不存活]
```

## 缓存机制

工具默认启用缓存机制，缓存文件保存在`cache_data`目录下。可以通过`--no-cache`选项禁用缓存，或通过`--cache-days`选项设置缓存有效期。

## 贡献

欢迎提交问题和贡献代码。

## 许可证

[MIT License](LICENSE) 