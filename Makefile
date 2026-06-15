# -*- coding: utf-8 -*-
#
# ARL项目 Makefile
# 开发、测试、部署命令
#

.PHONY: help install install-dev format lint typecheck test test-unit test-integration test-security migrate clean setup-dev

# 默认目标
help: ## 显示帮助信息
	@echo "ARL项目 - 可用命令"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 安装依赖
install: ## 安装生产依赖
	pip install -r requirements.txt

install-dev: ## 安装开发依赖
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# 代码格式化
format: ## 格式化代码 (black + isort)
	black app/ tests/ scripts/
	isort app/ tests/ scripts/

format-check: ## 检查代码格式
	black app/ tests/ --check
	isort app/ tests/ --check-only

# 代码检查
lint: ## 运行代码检查 (ruff)
	ruff check app/ tests/ scripts/

lint-fix: ## 自动修复代码检查问题
	ruff check app/ tests/ scripts/ --fix

# 类型检查
typecheck: ## 运行类型检查 (mypy)
	mypy app/ --ignore-missing-imports

# 测试
test: ## 运行所有测试
	pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: ## 运行单元测试
	pytest tests/unit/ -v --cov=app --cov-report=term-missing

test-integration: ## 运行集成测试
	pytest tests/integration/ -v --cov=app --cov-report=term-missing

test-security: ## 运行安全测试
	bandit -r app/ -f json -o reports/security.json
	@echo "安全报告已生成: reports/security.json"

test-coverage: ## 生成覆盖率报告
	pytest tests/ \
		--cov=app \
		--cov-report=term-missing \
		--cov-report=html:reports/coverage \
		--cov-report=xml:reports/coverage.xml \
		--cov-fail-under=80
	@echo "覆盖率报告已生成: reports/coverage/"

# 迁移
migrate: ## 运行架构迁移脚本
	python scripts/migrate_to_new_arch.py

migrate-passwords: ## 迁移MD5密码到bcrypt
	python scripts/migrate_md5_to_bcrypt.py

# 清理
clean: ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.egg-info" -delete 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache .coverage htmlcov
	rm -rf build dist *.egg-info
	@echo "清理完成"

clean-all: clean ## 清理所有（包括exports）
	rm -rf reports exports
	@echo "全部清理完成"

# 开发环境设置
setup-dev: ## 设置开发环境
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "开发环境设置完成"

# CI命令
ci: format-check lint typecheck test ## 运行完整的CI检查

# 默认Python命令
PYTHON = python
PYTEST = pytest
