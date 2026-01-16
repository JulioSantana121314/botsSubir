import os
import site

# Setup CUDA
for sp in site.getsitepackages():
    nvidia_path = os.path.join(sp, 'nvidia')
    if os.path.exists(nvidia_path):
        for subdir in os.listdir(nvidia_path):
            bin_path = os.path.join(nvidia_path, subdir, 'bin')
            if os.path.exists(bin_path):
                try:
                    os.add_dll_directory(bin_path)
                except:
                    pass
                os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')

import tensorflow as tf
import time
import numpy as np

print("="*70)
print("🔍 TEST DE GPU - TensorFlow 2.10")
print("="*70)

# 1. Detecta GPU
gpus = tf.config.list_physical_devices('GPU')
print(f"\n✅ GPUs detectadas: {len(gpus)}")
if gpus:
    for gpu in gpus:
        print(f"   {gpu.name}")
        tf.config.experimental.set_memory_growth(gpu, True)
else:
    print("❌ NO HAY GPU - Este test fallará")
    exit(1)

# 2. Operación forzada en GPU
print("\n🧪 Test 1: Operación forzada en GPU...")
with tf.device('/GPU:0'):
    a = tf.random.normal([5000, 5000])
    b = tf.random.normal([5000, 5000])
    
    start = time.time()
    c = tf.matmul(a, b)
    c.numpy()  # Fuerza ejecución
    gpu_time = time.time() - start

print(f"   ✅ Tiempo GPU: {gpu_time:.4f}s")

# 3. Compara con CPU
print("\n🧪 Test 2: Misma operación en CPU...")
with tf.device('/CPU:0'):
    a_cpu = tf.random.normal([5000, 5000])
    b_cpu = tf.random.normal([5000, 5000])
    
    start = time.time()
    c_cpu = tf.matmul(a_cpu, b_cpu)
    c_cpu.numpy()
    cpu_time = time.time() - start

print(f"   ✅ Tiempo CPU: {cpu_time:.4f}s")

# 4. Resultado
speedup = cpu_time / gpu_time
print(f"\n{'='*70}")
if speedup > 1.5:
    print(f"🚀 GPU ES {speedup:.1f}x MÁS RÁPIDA - ¡FUNCIONANDO!")
elif speedup > 1.0:
    print(f"⚠️ GPU ligeramente más rápida ({speedup:.1f}x) - puede estar limitada")
else:
    print(f"❌ CPU más rápida - GPU NO está siendo usada correctamente")
print(f"{'='*70}")

# 5. Test de entrenamiento real
print("\n🧪 Test 3: Mini-entrenamiento en GPU...")
with tf.device('/GPU:0'):
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(512, activation='relu', input_shape=(784,)),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(10, activation='softmax')
    ])
    
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
    
    # Datos dummy
    x_train = np.random.random((1000, 784))
    y_train = np.random.randint(0, 10, (1000,))
    
    start = time.time()
    model.fit(x_train, y_train, batch_size=32, epochs=3, verbose=0)
    train_time = time.time() - start

print(f"   ✅ 3 epochs en {train_time:.2f}s")
print(f"   {'✅ GPU ACTIVA' if train_time < 5 else '⚠️ Posible CPU fallback'}")

print("\n" + "="*70)
print("✅ TEST COMPLETADO")
print("="*70)
