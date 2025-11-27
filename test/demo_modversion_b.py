from demo_modversion_a import make_mod


def main() -> None:
    # 这里只导入 make_mod，没有导入 ModVersion
    mod = make_mod()

    # 依然可以访问实例的属性
    print(mod)
    print(vars(mod))
    print("mod.name =", mod.name)
    print("mod.zip_name =", mod.zip_name)
    print("mod.download_url =", mod.download_url)

    # 打印类型，看看它实际上是哪个类的实例
    print("type(mod) =", type(mod))


if __name__ == "__main__":
    main()
