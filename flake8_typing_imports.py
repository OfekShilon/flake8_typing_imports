import ast
import importlib.util
from typing import Any, ClassVar, Dict, Generator, List, Set, Tuple, Type

class TypeCheckingVisitor(ast.NodeVisitor):
    def __init__(self):
        # Track imports and their usage
        self.imports = {}  # module_name -> [imported_names]
        self.from_imports = {}  # from_module -> {name -> alias}
        self.star_imports = []  # list of modules with * imports
        self.type_checking_imports = set()  # names already in TYPE_CHECKING blocks
        
        # Track usage of imported names
        self.used_in_annotations = set()  # Names used in type annotations
        self.used_in_runtime = set()  # Names used in runtime code
        
        # Keep track of context
        self.in_annotation = False
        self.in_type_checking = False
        
    def visit_Import(self, node):
        if self.in_type_checking:
            for alias in node.names:
                self.type_checking_imports.add(alias.asname or alias.name)
        else:
            for alias in node.names:
                name = alias.asname or alias.name
                self.imports[name] = alias.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module == 'typing' and node.names[0].name == 'TYPE_CHECKING':
            # Skip importing TYPE_CHECKING itself
            return
            
        if self.in_type_checking:
            for alias in node.names:
                full_name = f"{alias.asname or alias.name}"
                self.type_checking_imports.add(full_name)
        else:
            if node.names[0].name == '*':
                self.star_imports.append(node.module)
            else:
                if node.module not in self.from_imports:
                    self.from_imports[node.module] = {}
                for alias in node.names:
                    self.from_imports[node.module][alias.name] = alias.asname or alias.name
        self.generic_visit(node)
    
    def visit_If(self, node):
        # Check if this is a TYPE_CHECKING block
        is_type_checking = False
        if isinstance(node.test, ast.Name) and node.test.id == 'TYPE_CHECKING':
            is_type_checking = True
        elif isinstance(node.test, ast.Constant) and node.test.value is False:
            # Sometimes people use `if False:  # TYPE_CHECKING` pattern
            is_type_checking = True
            
        old_in_tc = self.in_type_checking
        if is_type_checking:
            self.in_type_checking = True
            
        self.generic_visit(node)
        
        # Restore context
        self.in_type_checking = old_in_tc
    
    def visit_AnnAssign(self, node):
        # Track names used in annotations
        old_in_annotation = self.in_annotation
        self.in_annotation = True
        self.visit(node.annotation)
        self.in_annotation = old_in_annotation
        
        # Visit the value if it exists
        if node.value:
            self.visit(node.value)
    
    def visit_arg(self, node):
        # Function arguments with annotations
        if node.annotation:
            old_in_annotation = self.in_annotation
            self.in_annotation = True
            self.visit(node.annotation)
            self.in_annotation = old_in_annotation
    
    def visit_FunctionDef(self, node):
        # Function return annotations
        if node.returns:
            old_in_annotation = self.in_annotation
            self.in_annotation = True
            self.visit(node.returns)
            self.in_annotation = old_in_annotation
        
        # Visit the rest of the function
        for item in node.body:
            self.visit(item)
        
        # Visit decorators
        for decorator in node.decorator_list:
            self.visit(decorator)
    
    def visit_Name(self, node):
        # Track how names are used
        if node.id in self.imports or any(node.id in imports for imports in self.from_imports.values()):
            if self.in_annotation:
                self.used_in_annotations.add(node.id)
            else:
                self.used_in_runtime.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        # Handle attribute access like module.Class
        self.generic_visit(node)
        
        # If this is a direct module attribute, track its usage
        if isinstance(node.value, ast.Name) and node.value.id in self.imports:
            if self.in_annotation:
                self.used_in_annotations.add(node.value.id)
            else:
                self.used_in_runtime.add(node.value.id)


class TypeCheckingImportChecker:
    name = 'flake8-typing-imports'
    version = '0.1.0'
    
    def __init__(self, tree):
        self.tree = tree
    
    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = TypeCheckingVisitor()
        visitor.visit(self.tree)
        
        # Find names that are only used in type annotations
        type_only_names = set()
        
        # Check regular imports
        for name, module in visitor.imports.items():
            if name in visitor.used_in_annotations and name not in visitor.used_in_runtime:
                type_only_names.add(name)
        
        # Check from imports
        for module, names in visitor.from_imports.items():
            for original, alias in names.items():
                if alias in visitor.used_in_annotations and alias not in visitor.used_in_runtime:
                    type_only_names.add((module, original, alias))
        
        # Get line numbers for imports to report
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    import_name = name.asname or name.name
                    if import_name in type_only_names:
                        yield (
                            node.lineno,
                            node.col_offset,
                            f"TYP001 Import '{import_name}' is only used for type annotations. "
                            f"Consider moving it into 'if TYPE_CHECKING:' block",
                            type(self)
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                
                for name in node.names:
                    import_name = name.asname or name.name
                    if (node.module, name.name, import_name) in type_only_names:
                        yield (
                            node.lineno,
                            node.col_offset,
                            f"TYP001 Import '{import_name}' from '{node.module}' is only used for type annotations. "
                            f"Consider moving it into 'if TYPE_CHECKING:' block",
                            type(self)
                        )
