cart = [
    {"id": 1, "name": "iPhone", "price": 999},
    {"id": 2, "name": "iPad", "price": 599},
    {"id": 3, "name": "AirPods", "price": 199},
]

# 方法一：使用循环和del
# for i, toast in enumerate(cart):
#     if toast["id"] == 2:
#         del cart[i]  # 或 cart.pop(i)
#         break

# 方法二：使用列表推导式
# cart = [t for t in cart if t["id"] != 2]

# 方法三：使用filter函数
# cart = list(filter(lambda t: t["id"] != 2, cart))
# print(cart)

idx = next((i for i, item in enumerate(cart) if item["id"] == 2), -1)
print(idx)
