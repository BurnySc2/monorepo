# Only show root folder total size
du -sh /home/burny

# Show all folders (including root) with 1 level depth and their size, sorted in ascending order
du --max-depth=1 -h /home/burny | sort -h

# Show all folders (excluding root) with 1 level depth and their size, sorted in ascending order
du -sh /home/burny/* | sort -h
