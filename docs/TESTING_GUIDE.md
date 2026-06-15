# 测试指南

## 概述

本文档描述了ARL项目的测试策略、测试运行方法和测试覆盖率要求。

## 测试框架

- **测试框架**: pytest
- **覆盖率工具**: pytest-cov
- **覆盖率要求**: ≥80%

## 运行测试

### 运行所有测试

```bash
cd test
python main.py
```

### 使用pytest直接运行

```bash
pytest tests/
```

### 运行特定测试文件

```bash
pytest tests/test_file_utils.py
```

### 运行特定测试类

```bash
pytest tests/test_file_utils.py::TestLoadFile
```

### 运行特定测试方法

```bash
pytest tests/test_file_utils.py::TestLoadFile::test_load_existing_file
```

### 生成覆盖率报告

```bash
pytest --cov=app --cov-report=term-missing tests/
```

```bash
# 生成HTML报告
pytest --cov=app --cov-report=html tests/
```

## 测试类型

### 1. 单元测试

测试单个函数、工具、组件。

**示例**:
```python
def test_load_file():
    result = load_file("/path/to/file.txt")
    assert result == ["line1\n", "line2\n"]
```

**测试文件**:
- `tests/test_file_utils.py` - 文件工具函数测试
- `tests/test_string_utils.py` - 字符串工具函数测试
- `tests/test_path_utils.py` - 路径工具函数测试

### 2. 集成测试

测试API端点、数据库操作。

**示例**:
```python
def test_api_endpoint():
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
```

### 3. E2E测试

测试关键用户流程。

## 测试结构

### AAA模式

推荐使用 Arrange-Act-Assert 模式：

```python
def test_calculates_similarity_correctly():
    # Arrange
    vector1 = [1, 0, 0]
    vector2 = [0, 1, 0]

    # Act
    similarity = calculate_cosine_similarity(vector1, vector2)

    # Assert
    expect(similarity).to_be(0)
```

### 测试命名

使用描述性名称，解释测试的行为：

```python
def test_returns_empty_array_when_no_markets_match_query():
    ...

def test_throws_error_when_api_key_is_missing():
    ...

def test_falls_back_to_substring_search_when_redis_unavailable():
    ...
```

## 测试标记

使用 `pytest.mark` 对测试进行分类：

```python
@pytest.mark.unit
def test_calculate_total():
    ...

@pytest.mark.integration
def test_database_connection():
    ...

@pytest.mark.slow
def test_long_running_operation():
    ...
```

运行特定标记的测试：

```bash
pytest -m unit tests/
pytest -m integration tests/
pytest -m "not slow" tests/
```

## 测试覆盖率

### 覆盖率目标

- **最低覆盖率**: 80%
- **目标覆盖率**: 90%+
- **核心模块覆盖率**: 95%+

### 查看覆盖率

```bash
# 终端报告
pytest --cov=app --cov-report=term-missing tests/

# HTML报告
pytest --cov=app --cov-report=html tests/
# 打开 htmlcov/index.html

# XML报告（CI/CD）
pytest --cov=app --cov-report=xml tests/
```

### 覆盖率配置

在 `setup.cfg` 或 `pyproject.toml` 中配置：

```ini
[tool:pytest]
addopts = --cov=app --cov-report=term-missing --cov-fail-under=80
```

## 测试最佳实践

### 1. 测试隔离

每个测试应该独立运行，不依赖其他测试：

```python
# 好：独立的测试
def test_create_user():
    user = create_user(name="test")
    assert user.name == "test"

# 坏：依赖其他测试
def test_update_user():
    # 假设test_create_user已经运行
    user = get_user_by_id(1)
    update_user(user.id, name="updated")
    assert user.name == "updated"
```

### 2. 使用fixture

使用pytest fixture管理测试资源：

```python
@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content\n")
    return file

def test_read_file(temp_file):
    result = load_file(temp_file)
    assert result == ["content\n"]
```

### 3. 模拟外部依赖

使用 `unittest.mock` 或 `pytest-mock` 模拟外部依赖：

```python
from unittest.mock import patch

def test_api_call():
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {'status': 'ok'}
        result = fetch_data()
        assert result['status'] == 'ok'
```

### 4. 参数化测试

使用 `@pytest.mark.parametrize` 测试多组输入：

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("test", "TEST"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

## 持续集成

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml tests/
      - name: Check coverage
        run: coverage report --fail-under=80
```

## 常见问题

### 测试失败

1. 检查测试是否隔离
2. 检查模拟是否正确
3. 修复实现，而非测试（除非测试有误）

### 覆盖率不足

1. 识别未覆盖的代码
2. 编写针对未覆盖代码的测试
3. 排除不需要测试的代码（如配置、迁移）

### 测试运行缓慢

1. 使用 `@pytest.mark.slow` 标记慢速测试
2. 使用 `pytest-xdist` 并行运行测试
3. 减少不必要的I/O操作
