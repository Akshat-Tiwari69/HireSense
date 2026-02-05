# Theme Conversion Script for Interviewer & Proctor Dashboards
# Converts dark theme to light theme

# Interviewer Dashboard
$file1 = "f:\Code\cygnusa-elite-hire\frontend\src\pages\InterviewerDashboardPage.jsx"
if (Test-Path $file1) {
    $content = Get-Content $file1 -Raw
    
    # Main container
    $content = $content -replace 'bg-slate-900', 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'
    $content = $content -replace 'bg-gray-900', 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'
    
    # Header
    $content = $content -replace 'bg-slate-800/90', 'bg-white/80'
    $content = $content -replace 'border-slate-700', 'border-slate-200'
    
    # Cards
    $content = $content -replace 'bg-slate-800/50', 'bg-white shadow-md hover:shadow-xl transition-all duration-300'
    $content = $content -replace 'bg-slate-800', 'bg-white shadow-md'
    
    # Text colors
    $content = $content -replace 'text-slate-100', 'text-slate-900'
    $content = $content -replace 'text-slate-300', 'text-slate-700'
    $content = $content -replace 'text-slate-400', 'text-slate-600'
    
    # Borders
    $content = $content -replace 'border-slate-600', 'border-slate-300'
    
    Set-Content $file1 -Value $content -NoNewline
    Write-Host "✅ Interviewer Dashboard converted!" -ForegroundColor Green
}

# Proctor Dashboard
$file2 = "f:\Code\cygnusa-elite-hire\frontend\src\pages\ProctorDashboardPage.jsx"
if (Test-Path $file2) {
    $content = Get-Content $file2 -Raw
    
    # Main container
    $content = $content -replace 'bg-slate-900', 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'
    $content = $content -replace 'bg-gray-900', 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'
    
    # Header
    $content = $content -replace 'bg-slate-800/90', 'bg-white/80'
    $content = $content -replace 'border-slate-700', 'border-slate-200'
    
    # Cards
    $content = $content -replace 'bg-slate-800/50', 'bg-white shadow-md hover:shadow-xl transition-all duration-300'
    $content = $content -replace 'bg-slate-800', 'bg-white shadow-md'
    
    # Text colors
    $content = $content -replace 'text-slate-100', 'text-slate-900'
    $content = $content -replace 'text-slate-300', 'text-slate-700'
    $content = $content -replace 'text-slate-400', 'text-slate-600'
    
    # Borders
    $content = $content -replace 'border-slate-600', 'border-slate-300'
    
    Set-Content $file2 -Value $content -NoNewline
    Write-Host "✅ Proctor Dashboard converted!" -ForegroundColor Green
}

# Assessment Page
$file3 = "f:\Code\cygnusa-elite-hire\frontend\src\pages\AssessmentPage.jsx"
if (Test-Path $file3) {
    $content = Get-Content $file3 -Raw
    
    # Main container
    $content = $content -replace 'bg-slate-900', 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'
    $content = $content -replace 'bg-gray-900', 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50'
    
    # Cards
    $content = $content -replace 'bg-slate-800/50', 'bg-white shadow-md hover:shadow-xl transition-all duration-300'
    $content = $content -replace 'bg-slate-800', 'bg-white shadow-md'
    
    # Text colors
    $content = $content -replace 'text-slate-100', 'text-slate-900'
    $content = $content -replace 'text-slate-300', 'text-slate-700'
    $content = $content -replace 'text-slate-400', 'text-slate-600'
    
    # Borders
    $content = $content -replace 'border-slate-700', 'border-slate-200'
    $content = $content -replace 'border-slate-600', 'border-slate-300'
    
    Set-Content $file3 -Value $content -NoNewline
    Write-Host "✅ Assessment Page converted!" -ForegroundColor Green
}

Write-Host "`n🎉 All remaining dashboards converted to light theme!" -ForegroundColor Cyan
