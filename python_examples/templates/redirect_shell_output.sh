# To stdout example
echo 100

# To stderr example
cat file_doesnt_exist1

# Redirect stdout to stderr
echo 101 >&2
echo 101 1>&2

# Redirect stderr to stdout
cat file_doesnt_exist2 2>&1

# Suppress stdout
echo 200 >/dev/null
>/dev/null echo 201

# Suppress stderr
cat file_doesnt_exist3 2>/dev/null
2>/dev/null cat file_doesnt_exist4

# Suppress both by redirecting stdout to stderr and stderr to /dev/null
echo 300 2>/dev/null >&2
echo 301 2>/dev/null 1>&2

# Suppress both by redirecting stderr to stdout and stdout to /dev/null
cat file_doesnt_exist5 1>/dev/null 2>&1
cat file_doesnt_exist6 >/dev/null 2>&1
>/dev/null 2>&1 cat file_doesnt_exist7

# Suppress both by sending them both to /dev/null
cat file_doesnt_exist5 1>/dev/null 2>/dev/null
echo 400 1>/dev/null 2>/dev/null
