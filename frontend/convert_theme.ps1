# Theme Conversion Script for Admin Dashboard
# Converts dark theme to light theme

$file = "f:\Code\cygnusa-elite-hire\frontend\src\pages\AdminDashboardPage.jsx"
$content = Get-Content $file -Raw

# Main container background
$content = $content -replace 'bg-slate-900 text-slate-100', 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'

# Header
$content = $content -replace 'bg-slate-800/80 backdrop-blur-md border-b border-slate-700', 'bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm'

# Cards - primary style
$content = $content -replace 'bg-slate-800/50 border-slate-700', 'bg-white border-none shadow-md hover:shadow-xl transition-all duration-300'

# Dark cards
$content = $content -replace 'className="bg-slate-800 border-slate-700"', 'className="bg-white border-slate-200 shadow-md"'

# Tab list
$content = $content -replace 'className="bg-slate-800 border-slate-700"', 'className="bg-white border-slate-200 shadow-sm"'

# Tab trigger active state
$content = $content -replace 'data-\[state=active\]:bg-slate-700', 'data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700'

# Text colors
$content = $content -replace 'text-slate-400', 'text-slate-600'
$content = $content -replace 'text-slate-300', 'text-slate-700'
$content = $content -replace 'text-white">', 'text-slate-900">'
$content = $content -replace 'className="text-white"', 'className="text-slate-900"'

# Table rows and borders
$content = $content -replace 'border-slate-700', 'border-slate-200'

# Input and select backgrounds in dark theme
$content = $content -replace 'bg-slate-700/50', 'bg-white'
$content = $content -replace 'bg-slate-700', 'bg-slate-50'

# Border colors
$content = $content -replace 'border-slate-600', 'border-slate-300'

# Hover states
$content = $content -replace 'hover:bg-slate-700', 'hover:bg-indigo-50'
$content = $content -replace 'hover:bg-slate-800', 'hover:bg-slate-50'

Set-Content $file -Value $content -NoNewline
Write-Host "✅ Theme conversion complete!" -ForegroundColor Green
