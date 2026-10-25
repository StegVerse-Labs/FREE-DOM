if ! git diff --quiet -- data/master/; then
  echo "Canonical record mutation detected; refusing validation."
  git diff -- data/master/
  exit 1
fi
