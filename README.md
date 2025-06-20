# DeepX - 多接口集成的子域名收集工具

DeepX是一个功能强大的子域名收集工具，支持多个接口集成（OTX、CRT.sh、Archive.org、FOFA等），并具备增强型缓存机制和字典爆破功能。2.0版本引入了全新的缓存管理、多源数据比较和更智能的资产分类功能。

## 新版本主要更新

- **多源数据比较**：支持比较隐藏资产、FOFA资产和爆破结果，全面识别隐藏资产
- **增强型缓存机制**：基于时间戳的缓存文件管理，支持自动清理过期缓存
- **分类资产管理**：分别输出隐藏资产和总资产，便于资产梳理和管理
- **优化字典构建**：改进前缀提取算法，支持多级子域名前缀提取
- **流程优化**：重新设计执行流程，提高效率和准确性

## 功能特点

- **多源数据收集**：支持OTX、CRT.sh、Archive.org、FOFA等多个数据源
- **增强型缓存机制**：记录查询结果，提高查询效率，支持自动过期清理
- **分类缓存存储**：分别缓存隐藏资产和FOFA资产，提供更完整的查询历史
- **智能字典爆破**：从查询结果中提取子域名前缀，构建字典进行爆破
- **多级前缀提取**：支持提取多级子域名前缀，构建更全面的爆破字典
- **隐藏域名分析**：比较不同来源的结果，智能识别隐藏子域名
- **总资产输出**：提供隐藏资产和总资产的分类输出
- **彩色日志输出**：使用不同颜色区分不同类型的信息

## 安装方法

```bash
# 克隆仓库
git clone https://github.com/yourusername/DeepX.git
cd DeepX

# 安装依赖和配置
python setup.py

# 可选：设置FOFA API密钥
# 方法1：创建config/secrets.py文件并添加：FOFA_API_KEY = "your_key"
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

# 如果已安装为全局命令，也可以使用：
deepx example.com
deepx collect example.com
```

### 高级选项

```bash
# 禁用缓存
python DeepX.py collect example.com --no-cache

# 启用字典爆破（默认禁用）
python DeepX.py all example.com --enable-brute

# 设置缓存有效期（天）
python DeepX.py collect example.com --cache-days 7

# 指定输出文件
python DeepX.py collect example.com -o output/result.txt
```

## 配置说明

配置选项位于`config/config.py`文件中，包括：

- 缓存设置：缓存目录、有效期、自动清理等
- 字典爆破设置：字典目录、文件路径、并发数等
- FOFA API设置：API URL、并发限制、请求间隔等
- 输出文件：隐藏域名结果、总资产结果等

## 目录结构

```
DeepX/
├── __init__.py             # 初始化文件
├── __main__.py             # 主入口模块
├── DeepX.py                # 入口文件
├── setup.py                # 安装脚本
├── requirements.txt        # 依赖文件
├── README.md               # 说明文档
├── MANIFEST.in             # 打包配置文件
├── cache_data/             # 缓存数据目录
├── dict/                   # 字典文件目录
├── output/                 # 输出结果目录
├── core/                   # 核心功能模块
│   ├── __init__.py         # 核心包初始化
│   ├── core.py             # 核心功能实现
│   └── cli.py              # 命令行接口
├── cacher/                 # 缓存处理模块
│   ├── __init__.py         # 缓存包初始化
│   ├── manager.py          # 缓存管理器
│   └── dict_builder.py     # 字典构建器
├── collectors/             # 收集器模块
│   ├── __init__.py         # 收集器包初始化
│   ├── base.py             # 收集器基类
│   ├── crt.py              # CRT.sh收集器
│   ├── otx.py              # OTX收集器
│   ├── archive.py          # Archive.org收集器
│   ├── fofa.py             # FOFA收集器
│   └── factory.py          # 收集器工厂
├── config/                 # 配置管理模块
│   ├── __init__.py         # 配置包初始化
│   ├── config.py           # 配置定义
│   └── secrets.py          # 密钥配置（可选）
├── handlers/               # 结果处理模块
│   ├── __init__.py         # 处理器包初始化
│   ├── base.py             # 处理器基类
│   ├── console.py          # 控制台输出处理器
│   ├── file.py             # 文件输出处理器
│   └── comparison.py       # 比较处理器
└── utils/                  # 工具模块
    ├── __init__.py         # 工具包初始化
    ├── logger.py           # 日志工具
    └── formatter.py        # 格式化工具
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
- `-o, --output`: 输出文件名（默认: output/brute_subdomain.txt）

#### compare 命令 - 域名比较

```
python DeepX.py compare [-h] [-d] [--deep-file DEEP_FILE] [--fofa-file FOFA_FILE] [--brute-file BRUTE_FILE] [-r RESULT] [-t TOTAL] domain
```

- `domain`: 目标域名（仅用于日志显示）
- `-d, --debug`: 启用调试输出（默认启用）
- `--deep-file`: DeepX结果文件（默认: output/deep_subdomain.txt）
- `--fofa-file`: FOFA结果文件（默认: output/fofa_subdomain.txt）
- `--brute-file`: 爆破结果文件（默认: output/brute_subdomain.txt）
- `-r, --result`: 隐藏域名结果文件（默认: output/result.txt）
- `-t, --total`: 总资产结果文件（默认: output/total_subdomain.txt）

#### all 命令 - 完整流程

```
python DeepX.py all [-h] [-d] [--no-debug] [--key KEY] [--no-cache] [--cache-days DAYS] [--enable-brute] domain
```

- `domain`: 目标域名
- `-d, --debug`: 启用调试输出（默认启用）
- `--no-debug`: 禁用调试输出
- `--key`: FOFA API密钥（优先于环境变量）
- `--no-cache`: 禁用域名缓存
- `--cache-days`: 缓存有效期（天）
- `--enable-brute`: 启用字典爆破（默认禁用）

## 输出文件

- `output/deep_subdomain.txt`: 传统收集结果
- `output/fofa_subdomain.txt`: FOFA API收集结果
- `output/brute_subdomain.txt`: 字典爆破结果
- `output/result.txt`: 隐藏域名分析结果
- `output/total_subdomain.txt`: 总资产结果

## 缓存机制

- 缓存数据保存在`cache_data`目录中，文件名基于域名哈希和时间戳
- 缓存有效期默认为3天，可通过`--cache-days`参数或配置文件修改
- 缓存命中后会自动清理过期缓存（可在配置中禁用）
- 缓存分别保存隐藏资产和FOFA资产结果

## 示例

```bash
# 设置FOFA凭证
export FOFA_API_KEY="your_api_key"
export FOFA_EMAIL="your_email@example.com"

# 运行完整流程
python DeepX.py all example.com

# 运行完整流程并启用字典爆破
python DeepX.py all example.com --enable-brute
```

## 关于隐藏域名

隐藏域名是指那些在传统子域名收集方法中能够发现，但在FOFA等搜索引擎中无法索引到的子域名。这些域名通常具有更高的安全价值，可能包含内部系统、测试环境或未公开的资产。 