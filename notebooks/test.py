import torch
print(f"Versione Torch: {torch.__version__}")
print(f"CUDA disponibile: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"Capability: {torch.cuda.get_device_capability(0)}")
    # Prova un calcolo vero
    x = torch.randn(1, 3, 224, 224).cuda()
    model = torch.nn.Conv2d(3, 64, 3).cuda()
    out = model(x)
    print("🚀 TEST RIUSCITO: La 5060 calcola!")