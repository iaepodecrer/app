class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    def __init__(self):
        self.root = None
        
    def get_height(self, node):
        if not node:
            return 0
        return node.height
    
    def get_balance(self, node):
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)
    
    def right_rotate(self, z):
        y = z.left
        T2 = y.right

        # Realiza rotação
        y.right = z
        z.left = T2

        # Atualiza alturas
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y
    
    def left_rotate(self, z):
        y = z.right
        T2 = y.left

        # Realiza rotação
        y.left = z
        z.right = T2

        # Atualiza alturas
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y
    
    def insert(self, root, key):
        # Inserção BST padrão
        if not root:
            return Node(key)
        
        if key < root.key:
            root.left = self.insert(root.left, key)
        elif key > root.key:
            root.right = self.insert(root.right, key)
        else:  # Chaves iguais não são permitidas
            return root
        
        # Atualiza altura do ancestral
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        
        # Verifica o fator de balanceamento
        balance = self.get_balance(root)
        
        # Caso Left Left
        if balance > 1 and key < root.left.key:
            return self.right_rotate(root)
        
        # Caso Right Right
        if balance < -1 and key > root.right.key:
            return self.left_rotate(root)
        
        # Caso Left Right
        if balance > 1 and key > root.left.key:
            root.left = self.left_rotate(root.left)
            return self.right_rotate(root)
        
        # Caso Right Left
        if balance < -1 and key < root.right.key:
            root.right = self.right_rotate(root.right)
            return self.left_rotate(root)
        
        return root
    
    def min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current
    
    def delete(self, root, key):
        # Remoção BST padrão
        if not root:
            return root
        
        if key < root.key:
            root.left = self.delete(root.left, key)
        elif key > root.key:
            root.right = self.delete(root.right, key)
        else:
            # Nó com um filho ou sem filhos
            if not root.left:
                return root.right
            elif not root.right:
                return root.left
                
            # Nó com dois filhos
            temp = self.min_value_node(root.right)
            root.key = temp.key
            root.right = self.delete(root.right, temp.key)
        
        # Se a árvore tem apenas um nó
        if not root:
            return root
            
        # Atualiza altura
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        
        # Verifica o fator de balanceamento
        balance = self.get_balance(root)
        
        # Rebalanceamento
        # Caso Left Left
        if balance > 1 and self.get_balance(root.left) >= 0:
            return self.right_rotate(root)
        
        # Caso Left Right
        if balance > 1 and self.get_balance(root.left) < 0:
            root.left = self.left_rotate(root.left)
            return self.right_rotate(root)
        
        # Caso Right Right
        if balance < -1 and self.get_balance(root.right) <= 0:
            return self.left_rotate(root)
        
        # Caso Right Left
        if balance < -1 and self.get_balance(root.right) > 0:
            root.right = self.right_rotate(root.right)
            return self.left_rotate(root)
        
        return root
    
    def search(self, root, key):
        if not root or root.key == key:
            return root
            
        if root.key < key:
            return self.search(root.right, key)
            
        return self.search(root.left, key)
    
    def get_min(self, root):
        if not root:
            return None
        current = root
        while current.left:
            current = current.left
        return current.key
    
    def get_max(self, root):
        if not root:
            return None
        current = root
        while current.right:
            current = current.right
        return current.key
        
    # Métodos de conveniência para uso externo
    def insert_key(self, key):
        self.root = self.insert(self.root, key)
        
    def delete_key(self, key):
        self.root = self.delete(self.root, key)
        
    def search_key(self, key):
        return self.search(self.root, key)
        
    def find_min(self):
        return self.get_min(self.root)
        
    def find_max(self):
        return self.get_max(self.root)
