#!/usr/bin/env python3
"""
FastAPI Routes Validation Script

This script validates all FastAPI routes to ensure they are properly wired
with correct Pydantic models and have proper response schemas.
"""

import logging
import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class RouteInfo:
    """Information about a FastAPI route"""
    file_path: str
    method: str
    path: str
    function_name: str
    line_number: int
    request_model: str = None
    response_model: str = None
    dependencies: List[str] = None
    has_error_handling: bool = False
    issues: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.issues is None:
            self.issues = []

class FastAPIRouteValidator:
    """Validates FastAPI routes for proper model bindings and configurations"""
    
    def __init__(self):
        self.routes: List[RouteInfo] = []
        self.issues: List[str] = []
        self.validated_models: Set[str] = set()
    
    def validate_all_routes(self) -> Dict[str, Any]:
        """Validate all FastAPI routes in the application"""
        logger.info("🔍 Starting FastAPI routes validation...")
        
        # Define expected routes based on the agent directives
        expected_routes = {
            "GET /status": "analysis.py",
            "POST /code": "analysis.py", 
            "GET /patterns": "analysis.py",
            "GET /patterns/{pattern_name}": "analysis.py",
            "GET /insights/{repository_id}": "analysis.py",
            "GET /ai-models": "analysis.py",
            "POST /models/{model_id}/benchmark": "analysis.py",
            "POST /evolution": "analysis.py",
            "GET /compare/{repo_id1}/{repo_id2}": "analysis.py",
            "GET /models/available": "multi_model_analysis.py",
            "POST /analyze/single": "multi_model_analysis.py",
            "POST /analyze/compare": "multi_model_analysis.py",
            "POST /analyze/repository": "multi_model_analysis.py",
            "GET /comparison/{comparison_id}": "multi_model_analysis.py",
            "GET /models/{model_name}/stats": "multi_model_analysis.py",
            "POST /models/{model_name}/estimate-cost": "multi_model_analysis.py",
            "POST /submit": "repositories.py",
            "GET /": "repositories.py",
            "POST /": "repositories.py"
        }
        
        # Validate each API file
        api_files = [
            "backend/app/api/analysis.py",
            "backend/app/api/multi_model_analysis.py", 
            "backend/app/api/repositories.py",
            "backend/app/api/auth.py"
        ]
        
        for file_path in api_files:
            self._validate_api_file(file_path)
        
        # Check for expected routes
        self._check_expected_routes(expected_routes)
        
        # Validate model consistency
        self._validate_model_consistency()
        
        # Generate validation report
        return self._generate_validation_report()
    
    def _validate_api_file(self, file_path: str):
        """Validate a single API file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._validate_route_function(node, file_path)
                    
        except Exception as e:
            self.issues.append(f"Error parsing {file_path}: {e}")
    
    def _validate_route_function(self, func_node: ast.FunctionDef, file_path: str):
        """Validate a route function"""
        # Check if this is a route function
        if not self._is_route_function(func_node):
            return
        
        route_info = RouteInfo(
            file_path=file_path,
            method="",
            path="",
            function_name=func_node.name,
            line_number=func_node.lineno
        )
        
        # Extract decorator information
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if hasattr(decorator.func, 'attr'):
                    route_info.method = decorator.func.attr.upper()
                
                # Extract path from decorator arguments
                for arg in decorator.args:
                    if isinstance(arg, ast.Constant):
                        route_info.path = arg.value
                    elif isinstance(arg, ast.Str):  # Python < 3.8
                        route_info.path = arg.s
        
        # Extract function parameters and their types
        self._extract_function_info(func_node, route_info)
        
        # Validate route configuration
        self._validate_route_config(route_info)
        
        self.routes.append(route_info)
    
    def _is_route_function(self, func_node: ast.FunctionDef) -> bool:
        """Check if a function is a FastAPI route"""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if hasattr(decorator.func, 'attr') and decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                    return True
        return False
    
    def _extract_function_info(self, func_node: ast.FunctionDef, route_info: RouteInfo):
        """Extract information from function parameters and annotations"""
        for arg in func_node.args.args:
            if arg.annotation:
                type_str = ast.unparse(arg.annotation)
                
                # Check for request models
                if 'Request' in type_str or 'BaseModel' in type_str:
                    route_info.request_model = type_str
                
                # Check for dependencies
                if 'Depends' in type_str:
                    route_info.dependencies.append(type_str)
        
        # Check for response_model in decorators
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                for keyword in decorator.keywords:
                    if keyword.arg == 'response_model':
                        if isinstance(keyword.value, ast.Name):
                            route_info.response_model = keyword.value.id
                        elif isinstance(keyword.value, ast.Attribute):
                            route_info.response_model = ast.unparse(keyword.value)
    
    def _validate_route_config(self, route_info: RouteInfo):
        """Validate route configuration"""
        issues = []
        
        # Check for proper HTTP method
        if not route_info.method:
            issues.append("Missing HTTP method in decorator")
        
        # Check for path definition
        if not route_info.path:
            issues.append("Missing path in route decorator")
        
        # Check for async function
        # Note: This would require checking the function definition, which is complex in AST
        
        # Check for error handling
        # Note: This would require analyzing the function body
        
        route_info.issues = issues
    
    def _check_expected_routes(self, expected_routes: Dict[str, str]):
        """Check if all expected routes are present"""
        found_routes = set()
        
        for route in self.routes:
            route_key = f"{route.method} {route.path}"
            found_routes.add(route_key)
        
        missing_routes = []
        for expected_route, expected_file in expected_routes.items():
            if expected_route not in found_routes:
                missing_routes.append(f"{expected_route} (expected in {expected_file})")
        
        if missing_routes:
            self.issues.extend([f"Missing expected route: {route}" for route in missing_routes])
    
    def _validate_model_consistency(self):
        """Validate model consistency across routes"""
        # Check for proper model imports
        model_files = [
            "backend/app/models/repository.py",
            "backend/app/models/ai_models.py",
            "backend/app/schemas/repository.py"
        ]
        
        available_models = set()
        for model_file in model_files:
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and self._is_pydantic_model(node):
                        available_models.add(node.name)
                        
            except Exception as e:
                self.issues.append(f"Error parsing model file {model_file}: {e}")
        
        # Check if referenced models exist
        for route in self.routes:
            if route.request_model and route.request_model not in available_models:
                route.issues.append(f"Request model '{route.request_model}' not found")
            
            if route.response_model and route.response_model not in available_models:
                route.issues.append(f"Response model '{route.response_model}' not found")
    
    def _is_pydantic_model(self, class_node: ast.ClassDef) -> bool:
        """Check if a class is a Pydantic model"""
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                if base.id in ['BaseModel', 'Model']:
                    return True
            elif isinstance(base, ast.Attribute):
                if base.attr in ['BaseModel', 'Model']:
                    return True
        return False
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        total_routes = len(self.routes)
        routes_with_issues = sum(1 for route in self.routes if route.issues)
        
        report = {
            "validation_timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_routes_found": total_routes,
                "routes_with_issues": routes_with_issues,
                "routes_valid": total_routes - routes_with_issues,
                "validation_success": len(self.issues) == 0 and routes_with_issues == 0
            },
            "routes": [
                {
                    "file": route.file_path,
                    "method": route.method,
                    "path": route.path,
                    "function": route.function_name,
                    "line": route.line_number,
                    "request_model": route.request_model,
                    "response_model": route.response_model,
                    "dependencies": route.dependencies,
                    "issues": route.issues
                }
                for route in self.routes
            ],
            "global_issues": self.issues,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for fixing issues"""
        recommendations = []
        
        if self.issues:
            recommendations.append("🚨 Fix global validation issues")
        
        routes_with_issues = [route for route in self.routes if route.issues]
        if routes_with_issues:
            recommendations.append("🔧 Fix route-specific issues")
            recommendations.append("📝 Add proper request/response models where missing")
            recommendations.append("🛡️ Add error handling to routes")
        
        recommendations.extend([
            "✅ Ensure all routes have proper type annotations",
            "📊 Add response_model to all routes for better API documentation",
            "🔍 Add comprehensive error handling with proper HTTP status codes",
            "📚 Update OpenAPI documentation to reflect all routes",
            "🧪 Create integration tests for all routes"
        ])
        
        return recommendations

def main():
    """Main validation function"""
    logging.basicConfig(level=logging.INFO)
    
    validator = FastAPIRouteValidator()
    report = validator.validate_all_routes()
    
    # Print summary
    print("🔍 FastAPI Routes Validation Report")
    print("=" * 60)
    print(f"📊 Total routes found: {report['summary']['total_routes_found']}")
    print(f"✅ Valid routes: {report['summary']['routes_valid']}")
    print(f"❌ Routes with issues: {report['summary']['routes_with_issues']}")
    print(f"🎯 Validation success: {report['summary']['validation_success']}")
    print()
    
    if report['global_issues']:
        print("🚨 GLOBAL ISSUES:")
        for issue in report['global_issues']:
            print(f"  - {issue}")
        print()
    
    routes_with_issues = [route for route in report['routes'] if route['issues']]
    if routes_with_issues:
        print("🔧 ROUTES WITH ISSUES:")
        for route in routes_with_issues:
            print(f"  {route['method']} {route['path']} ({route['function']})")
            for issue in route['issues']:
                print(f"    - {issue}")
        print()
    
    print("📋 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Save detailed report
    import json
    with open('fastapi_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: fastapi_validation_report.json")
    
    return 0 if report['summary']['validation_success'] else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
