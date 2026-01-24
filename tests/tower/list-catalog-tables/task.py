import os
from pyiceberg.catalog import load_catalog


def list_catalog_contents(catalog_name: str = "default"):
    print(f"Connecting to catalog: {catalog_name}")
    print("=" * 60)

    try:
        catalog = load_catalog(catalog_name)
    except Exception as e:
        print(f"Error loading catalog '{catalog_name}': {e}")
        print("\nMake sure you have a catalog configured in Tower.")
        return

    print(f"Catalog type: {type(catalog).__name__}")

    print("\n NAMESPACES")
    print("-" * 40)

    try:
        namespaces = catalog.list_namespaces()
        if not namespaces:
            print("  (no namespaces found)")
        else:
            for ns in namespaces:
                namespace_name = ".".join(ns) if isinstance(ns, tuple) else str(ns)
                print(f"  • {namespace_name}")

        print("\n TABLES BY NAMESPACE")
        print("-" * 40)

        total_tables = 0
        show_details = os.environ.get("SHOW_DETAILS", "false").lower() == "true"

        for ns in namespaces:
            namespace_name = ".".join(ns) if isinstance(ns, tuple) else str(ns)

            try:
                tables = catalog.list_tables(ns)

                if tables:
                    print(f"\n  [{namespace_name}]")
                    for table_id in tables:
                        if hasattr(table_id, "name"):
                            table_name = table_id.name
                        elif isinstance(table_id, tuple):
                            table_name = str(table_id[-1])
                        else:
                            table_name = str(table_id)
                        print(f"    └─ {table_name}")
                        total_tables += 1

                        if show_details:
                            try:
                                table = catalog.load_table(table_id)
                                schema = table.schema()
                                print(f"       Schema: {len(schema.fields)} columns")
                                for field in schema.fields[:5]:
                                    print(f"         - {field.name}: {field.field_type}")
                                if len(schema.fields) > 5:
                                    print(f"         ... and {len(schema.fields) - 5} more columns")
                            except Exception as e:
                                print(f"       (could not load schema: {e})")
                else:
                    print(f"\n  [{namespace_name}]")
                    print("    (no tables)")

            except Exception as e:
                print(f"\n  [{namespace_name}]")
                print(f"    (error listing tables: {e})")

        print("\n" + "=" * 60)
        print(" SUMMARY")
        print(f"   Namespaces: {len(namespaces)}")
        print(f"   Total Tables: {total_tables}")
        print("=" * 60)

    except Exception as e:
        print(f"Error listing catalog contents: {e}")
        raise


def main():
    catalog_name = os.environ.get("CATALOG_NAME", "default")
    list_catalog_contents(catalog_name)


if __name__ == "__main__":
    main()
