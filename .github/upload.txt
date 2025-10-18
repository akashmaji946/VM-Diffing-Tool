# from repo root
git fetch origin

# 1) Create a temporary branch from the site/ subtree
git subtree split --prefix site -b gh-pages-tmp

# 2) Push it as the new gh-pages branch (force to create/update)
git push -f origin gh-pages-tmp:gh-pages

# 3) Clean up the temp branch locally
git branch -D gh-pages-tmp