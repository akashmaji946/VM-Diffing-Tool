import vmtool

meta = vmtool.get_meta_data("/home/akashmaji/Desktop/vm1.qcow2", verbose=False)


print()
print("===========================================================")
print("Totals:")
print("  files:", meta["files_count"])
print("  dirs:", meta["dirs_count"])
print("  total_file_bytes:", meta["total_file_bytes"])
print("  total_dir_bytes:", meta["total_dir_bytes"])
print("  total_bytes:", meta["total_bytes"])

print("===========================================================")
print("\nUsers (all, including zero):")
for row in meta["per_user"]:
    print(f"  {row['user']} (uid={row['uid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")

print("===========================================================")
print("\nGroups (all, including zero):")
for row in meta["per_group"]:
    print(f"  {row['group']} (gid={row['gid']}): files={row['files']} dirs={row['dirs']} bytes={row['bytes']}")

print("===========================================================")
print("Done.")
