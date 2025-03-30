#ifndef OBJECTPOOL_H
#define OBJECTPOOL_H

#include <vector>
#include <memory>
#include <functional>

template <typename T>
class ObjectPool {
public:
    // Custom deleter para que ao deletar o ponteiro ele seja retornado à pool
    struct PoolDeleter {
        ObjectPool<T>* pool;
        void operator()(T* ptr) {
            pool->release(ptr);
        }
    };

    using Ptr = std::unique_ptr<T, PoolDeleter>;

    ObjectPool() = default;

    // Obtém um objeto disponível ou aloca um novo se necessário
    Ptr acquire() {
        if (!pool_.empty()) {
            T* obj = pool_.back();
            pool_.pop_back();
            return Ptr(obj, PoolDeleter{this});
        }
        T* newObj = new T();
        return Ptr(newObj, PoolDeleter{this});
    }

    // Libera o objeto retornando-o à pool
    void release(T* obj) {
        // Se necessário, restabelecer o estado do objeto antes de reutilizar
        // Por exemplo: obj->clear(); ou qualquer método de reset.
        pool_.push_back(obj);
    }

    // Libera todos os objetos armazenados na pool
    ~ObjectPool() {
        for (T* obj : pool_) {
            delete obj;
        }
    }

private:
    std::vector<T*> pool_;
};

#endif // OBJECTPOOL_H
