#!/bin/bash

set -e

echo "🚀 Subtree push start..."

# Component Designer
echo "📦 Pushing component-designer..."
git subtree push --prefix=modules/component_designer https://github.com/HakanSeven12/Component-Designer main

# LandXML
echo "📦 Pushing landxml..."
git subtree push --prefix=modules/landxml https://github.com/HakanSeven12/LandXML main

echo "✅ Tüm subtree push done."
