# Find all image files and count the result
find . -iregex '.*\.\(jpg\|jpeg\|png\)' | wc -l

# Find all files ending with "hello.py" (case insensitive)
find . -iname "*hello.py"

# Find and delete empty folders
find ~/Downloads/ -empty -type d -delete

# In current git repository, find all python files in subfolder "fastapi_server"
git ls-files '*.py' | grep fastapi_server
# In current git repository, find all python files in test folders or that contain "test" in their filename
git ls-files '*.py' | grep -E '.*test.*'
