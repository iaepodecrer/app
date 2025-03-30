def binary_search(arr, target):
    """
    Busca binária: retorna o índice de target em arr se presente ou -1 se não encontrado.
    """
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

if __name__ == "__main__":
    # Exemplo de dados
    data = [34, 7, 23, 32, 5, 62, 23, 8]
    # Ordena a lista de dados antes de aplicar a busca binária
    data.sort()
    print("Dados ordenados:", data)
    
    # Elemento a ser buscado
    target = 23
    index = binary_search(data, target)
    if index != -1:
        print(f"Elemento {target} encontrado na posição {index}.")
    else:
        print(f"Elemento {target} não encontrado.")
    
    # Teste adicional para um elemento que não existe
    missing = 100
    result = binary_search(data, missing)
    if result != -1:
        print(f"Elemento {missing} encontrado inesperadamente na posição {result}.")
    else:
        print(f"Elemento {missing} não encontrado, conforme esperado.")
