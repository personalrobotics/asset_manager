
from asset_manager.manager import AssetManager

def main():
    am = AssetManager("data/objects", verbose=True)
    am.summary()
    print("Modules:", am.modules())
    print("Cup MuJoCo path:", am.get_path("cup", "mujoco"))

if __name__ == "__main__":
    main()
