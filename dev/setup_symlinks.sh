#!/bin/bash

cd "$(dirname "$0")/.." # move to `sindri`

# Link `PowerSpectra` to `loki`
if [ ! -L PowerSpectra ]; then
  ln -s loki PowerSpectra
  echo "Created symlink: PowerSpectra -> loki"
else
  echo "Symlink already exists: PowerSpectra"
fi

# Link `CorrelationFunctions` to `thor`
if [ ! -L CorrelationFunctions ]; then
  ln -s thor CorrelationFunctions
  echo "Created symlink: CorrelationFunctions -> thor"
else
  echo "Symlink already exists: CorrelationFunctions"
fi
