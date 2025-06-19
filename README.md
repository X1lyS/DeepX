# DeepX - 多接口集成的子域名收集工具

DeepX是一个功能强大的子域名收集工具，支持多个接口集成（OTX、CRT.sh、Archive.org、FOFA等），并具备缓存机制和字典爆破功能。

## 功能特点

- 支持多种接口：OTX、CRT.sh、Archive.org、FOFA等
- 缓存机制：记录查询结果，提高查询效率
- 字典爆破：从查询结果中提取子域名前缀，构建字典进行爆破
- 彩色日志输出：使用不同颜色区分不同类型的信息
- 隐藏域名分析：比较不同来源的结果，发现隐藏子域名

## 安装方法

```bash
# 克隆仓库
git clone https://github.com/yourusername/DeepX.git
cd DeepX

# 安装依赖
pip install -r requirements.txt

# 可选：设置FOFA API密钥
# 方法1：创建secrets.py文件并添加：FOFA_API_KEY = "your_key"
# 方法2：设置环境变量：export FOFA_API_KEY="your_key"
```

## 使用方法

### 基本用法

```bash
# 使用所有收集器
python DeepX.py example.com

# 使用指定命令
python DeepX.py collect example.com
python DeepX.py fofa example.com
python DeepX.py brute example.com
python DeepX.py compare example.com
python DeepX.py all example.com
```

### 高级选项

```bash
# 禁用缓存
python DeepX.py collect example.com --no-cache

# 禁用字典爆破
python DeepX.py collect example.com --no-brute

# 设置缓存有效期（天）
python DeepX.py collect example.com --cache-days 7

# 指定输出文件
python DeepX.py collect example.com -o output/result.txt
```

## 配置说明

配置选项位于`config.py`文件中，包括：

- 缓存设置：缓存目录、有效期等
- 字典爆破设置：字典文件路径、并发数等
- FOFA API设置：API URL、并发限制等

## 目录结构

```
DeepX/
├── __init__.py           # 初始化文件
├── __main__.py           # 主入口模块
├── cli.py                # 命令行界面
├── core.py               # 核心功能
├── config.py             # 配置管理
├── secrets.py            # 密钥配置（可选）
├── DeepX.py              # 入口文件
├── setup.py              # 安装脚本
├── requirements.txt      # 依赖文件
├── README.md             # 说明文档
├── cache/                # 缓存模块
├── dict/                 # 字典目录
├── collectors/           # 收集器模块
├── handlers/             # 处理器模块
└── utils/                # 工具模块
```

## 环境变量

- `FOFA_API_KEY`: FOFA API密钥
- `FOFA_EMAIL`: FOFA账号邮箱

## 命令选项

#### collect 命令 - 传统收集

```
python DeepX.py collect [-h] [-d] [--no-debug] [-o OUTPUT] [--collectors OTX CRT ARCHIVE] domain
```

- `domain`: 目标域名
- `-d, --debug`: 启用调试输出（默认启用）
- `--no-debug`: 禁用调试输出
- `-o, --output`: 输出文件名（默认: output/deep_subdomain.txt）
- `--collectors`: 指定要使用的收集器（可选：otx, crt, archive）
- `--no-cache`: 禁用域名缓存
- `--cache-days`: 缓存有效期（天）
- `--no-brute`: 禁用字典爆破

#### fofa 命令 - FOFA API收集

```
python DeepX.py fofa [-h] [-d] [--no-debug] [-o OUTPUT] [--key KEY] [--email EMAIL] domain
```

- `domain`: 目标域名
- `-d, --debug`: 启用调试输出（默认启用）
- `--no-debug`: 禁用调试输出
- `-o, --output`: 输出文件名（默认: output/fofa_subdomain.txt）
- `--key`: FOFA API密钥（优先于环境变量）
- `--email`: FOFA账号邮箱（优先于环境变量）

#### brute 命令 - 字典爆破

```
python DeepX.py brute [-h] [-d] [--no-debug] [-o OUTPUT] domain
```

- `domain`: 目标域名
- `-d, --debug`: 启用调试输出（默认启用）
- `--no-debug`: 禁用调试输出
- `-o, --output`: 输出文件名（默认: brute_results.txt）

#### compare 命令 - 域名比较

```
python DeepX.py compare [-h] [-d] [--deep-file DEEP_FILE] [--fofa-file FOFA_FILE] [-r RESULT] domain
```

- `domain`: 目标域名（仅用于日志显示）
- `-d, --debug`: 启用调试输出（默认启用）
- `--deep-file`: DeepX结果文件（默认: output/deep_subdomain.txt）
- `--fofa-file`: FOFA结果文件（默认: output/fofa_subdomain.txt）
- `-r, --result`: 隐藏域名结果文件（默认: output/result.txt）

#### all 命令 - 完整流程

```
python DeepX.py all [-h] [-d] [--no-debug] [--key KEY] [--email EMAIL] [--no-cache] [--no-brute] domain
```

- `domain`: 目标域名
- `-d, --debug`: 启用调试输出（默认启用）
- `--no-debug`: 禁用调试输出
- `--key`: FOFA API密钥（优先于环境变量）
- `--email`: FOFA账号邮箱（优先于环境变量）
- `--no-cache`: 禁用域名缓存
- `--no-brute`: 禁用字典爆破

## 输出文件

- `output/deep_subdomain.txt`: 传统收集结果
- `output/fofa_subdomain.txt`: FOFA API收集结果
- `output/result.txt`: 隐藏域名分析结果

## 示例

```bash
# 设置FOFA凭证
export FOFA_API_KEY="your_api_key"
export FOFA_EMAIL="your_email@example.com"

# 运行完整流程
python DeepX.py all example.com
```

## 关于隐藏域名

隐藏域名是指那些在传统子域名收集方法中能够发现，但在FOFA等搜索引擎中无法索引到的子域名。这些域名通常具有更高的安全价值，可能包含内部系统、测试环境或未公开的资产。 