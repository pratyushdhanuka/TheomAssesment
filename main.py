from KVStore import KVStore


def main():
    store = KVStore("node1", ["node2", "node3"])
    store.put("user:1", {"name": "Alice", "email": "alice@example.com"})
    print(store.get("user:1"))


if __name__ == "__main__":
    main()
