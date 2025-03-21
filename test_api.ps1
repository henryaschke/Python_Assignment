# PowerShell script to test all API endpoints
Write-Host "Willkommen zu Professor Alberto's Energie Handelsplattform Test!" -ForegroundColor Cyan
Write-Host "Testing Energy Trading API Endpoints - Mit deutscher Praezision!" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000/api"
$credentials = @{
    email = "admin@example.com"
    password = "admin123"
}

# Helper function to make API calls
function Invoke-ApiCall {
    param (
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [string]$Token = $null
    )
    
    $headers = @{}
    if ($Token) {
        $headers["Authorization"] = "Bearer $Token"
    }

    $params = @{
        Uri = "$baseUrl$Endpoint"
        Method = $Method
        Headers = $headers
        ContentType = "application/json"
    }

    if ($Body -and $Method -ne "GET") {
        $params["Body"] = ($Body | ConvertTo-Json)
    }

    try {
        # A little German encouragement
        if ($Method -eq "GET") {
            Write-Host "Daten werden geholt... (Getting data from endpoint: $Endpoint)" -ForegroundColor DarkGray
        } else {
            Write-Host "Daten werden gesendet... (Sending data to endpoint: $Endpoint)" -ForegroundColor DarkGray
        }
        
        $response = Invoke-RestMethod @params
        
        # Handle case where response is a JSON string instead of an object
        if ($response -is [string] -and $response.StartsWith('[') -and $response.EndsWith(']')) {
            try {
                $response = $response | ConvertFrom-Json -ErrorAction SilentlyContinue
            } catch {
                Write-Host "Achtung! Could not parse response as JSON: $_" -ForegroundColor Yellow
            }
        }
        
        return $response
    }
    catch {
        Write-Host "Fehler beim Aufrufen von $Endpoint! Das ist nicht gut! (Error calling endpoint)" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host $_.ErrorDetails.Message -ForegroundColor Red
        }
        return $null
    }
}

# Test status endpoint
Write-Host "`nSystem-Status wird ueberprueft (Checking system status):" -ForegroundColor Green
Write-Host "Endpoint: /status" -ForegroundColor Gray
$status = Invoke-ApiCall -Method "GET" -Endpoint "/status"
Write-Host "Status: $($status.status) - Alles klar, Herr Professor Alberto!"
Write-Host "Datenbank verbunden (Database connected): $($status.database.connected) - Wunderbar!"

# Authenticate and get token
Write-Host "`nAuthentifizierung laeuft (Authentication in progress):" -ForegroundColor Green
Write-Host "Endpoint: /auth/login" -ForegroundColor Gray
$authResponse = Invoke-ApiCall -Method "POST" -Endpoint "/auth/login" -Body $credentials
if ($authResponse) {
    Write-Host "Authentifizierung erfolgreich! (Authentication successful) Sehr gut!"
    $token = $authResponse.access_token
    Write-Host "Token received: $($token.Substring(0, 15))... Streng geheim! (Top secret!)"

    # Test getting user info
    Write-Host "`nBenutzerinfo wird abgerufen (Getting user info):" -ForegroundColor Green
    Write-Host "Endpoint: /auth/me" -ForegroundColor Gray
    $userInfo = Invoke-ApiCall -Method "GET" -Endpoint "/auth/me" -Token $token
    Write-Host "Benutzer-Email (User email): $($userInfo.email) - Guten Tag!"
    Write-Host "Benutzername (Username): $($userInfo.name) - Herzlich Willkommen!"
    
    # Test battery status
    Write-Host "`nBatteriestatus wird ueberprueft (Checking battery status - Very important for Professor Alberto!):" -ForegroundColor Green
    Write-Host "Endpoint: /battery/status" -ForegroundColor Gray
    $batteryStatus = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
    if ($batteryStatus) {
        Write-Host "Aktueller Ladestand (Current level): $($batteryStatus.level)% - Fantastisch!"
        Write-Host "Gesamtkapazitaet (Total capacity): $($batteryStatus.capacity.total) kWh - Beeindruckend!"
        Write-Host "Verbrauchte Kapazitaet (Used capacity): $($batteryStatus.capacity.used) kWh - Interessant!"
        Write-Host "Verbleibende Kapazitaet (Remaining capacity): $($batteryStatus.capacity.remaining) kWh - Noch genug Saft!"
        Write-Host "Prozentsatz (Percentage): $($batteryStatus.capacity.percentage)% - Danke fuer die Praezision!"
    }
    
    # Test market data - today
    Write-Host "`nMarktdaten von heute werden abgerufen (Fetching today's market data - The market never sleeps!):" -ForegroundColor Green
    Write-Host "Endpoint: /market-data/today" -ForegroundColor Gray
    $marketData = Invoke-ApiCall -Method "GET" -Endpoint "/market-data/today" -Token $token
    Write-Host "$($marketData.Count) Marktdaten-Eintraege abgerufen (market data entries retrieved) - Sehr effizient!"
    if ($marketData.Count -gt 0) {
        Write-Host "Erster Eintrag (First entry): Lieferzeit: $($marketData[0].delivery_period), Preis: $($marketData[0].close) - Sehr interessant fuer Professor Alberto!"
    }
    
    # Test market data - current
    Write-Host "`nAktuelle Marktdaten werden abgerufen (Getting current market data - Snapshot of the market!):" -ForegroundColor Green
    Write-Host "Endpoint: /market-data/current" -ForegroundColor Gray
    $currentMarketData = Invoke-ApiCall -Method "GET" -Endpoint "/market-data/current" -Token $token
    if ($currentMarketData) {
        # Different APIs return price in different properties
        $price = if ($currentMarketData.price) { 
            $currentMarketData.price 
        } elseif ($currentMarketData.close) { 
            $currentMarketData.close 
        } elseif ($currentMarketData.close_price) { 
            $currentMarketData.close_price 
        } else { 
            "N/A" 
        }
        
        Write-Host "Aktueller Preis (Current price): $price - Das ist ja ein Schnaeppchen!"
        Write-Host "Lieferzeit (Delivery period): $($currentMarketData.delivery_period) - Puenktlich wie die deutsche Bahn... hoffentlich!"
        Write-Host "Status: $($currentMarketData.status) - Alles unter Kontrolle!"
        Write-Host "Markt (Market): $($currentMarketData.market) - Der klassische Energiemarkt!"
    }
    
    # Test forecast
    Write-Host "`nPreisprognose wird ueberprueft (Checking price forecast - Looking into the future, very German!):" -ForegroundColor Green
    Write-Host "Endpoint: /forecast/price" -ForegroundColor Gray
    $forecast = Invoke-ApiCall -Method "GET" -Endpoint "/forecast/price" -Token $token
    if ($forecast) {
        Write-Host "$($forecast.Count) Prognoseeintraege abgerufen (forecast entries retrieved) - Ordnung muss sein!"
        if ($forecast.Count -gt 0) {
            # Check both possible property names for price
            $priceValue = if ($forecast[0].price) { 
                $forecast[0].price 
            } elseif ($forecast[0].predicted_price) { 
                $forecast[0].predicted_price 
            } else { 
                "N/A" 
            }
            Write-Host "Erste Prognose (First forecast): Zeit: $($forecast[0].timestamp), Preis: $priceValue - So genau wie ein Schweizer Uhrwerk!"
        }
    }
    
    # Test forecast accuracy
    Write-Host "`nGenauigkeit der Prognose wird ueberprueft (Testing forecast accuracy - How precise is our crystal ball?):" -ForegroundColor Green
    Write-Host "Endpoint: /forecast/accuracy" -ForegroundColor Gray
    $accuracy = Invoke-ApiCall -Method "GET" -Endpoint "/forecast/accuracy" -Token $token
    if ($accuracy) {
        Write-Host "Zeitraum (Period): $($accuracy.period) - Eine gute Zeitspanne!"
        Write-Host "MAPE: $($accuracy.mape)% - Professor Alberto waere stolz auf diese Genauigkeit!"
    }

    # Test electricity trading endpoints
    Write-Host "`nStromhandel wird getestet (Testing electricity trading - Now it gets exciting!):" -ForegroundColor Green
    
    # First check current battery level
    $batteryBefore = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
    if ($batteryBefore) {
        Write-Host "Anfaenglicher Batteriestand (Initial battery level): $($batteryBefore.level)% - Der Ausgangspunkt!"
        Write-Host "Anfaengliche Energie (Initial energy): $($batteryBefore.capacity.used) kWh - Potenzial fuer Gewinn!"
        
        # Test buying electricity
        Write-Host "`n  Stromkauf wird getestet (Testing buying electricity - Shopping like at the weekly market!):" -ForegroundColor Yellow
        Write-Host "  Endpoint: /trades/buy" -ForegroundColor Gray
        $buyRequest = @{
            quantity = 10.0  # Buy 10 kWh
            price = 40.0     # Set a specific price
        }
        Write-Host "  Request data: quantity = $($buyRequest.quantity) kWh, price = $($buyRequest.price)" -ForegroundColor Gray
        $buyResult = Invoke-ApiCall -Method "POST" -Endpoint "/trades/buy" -Body $buyRequest -Token $token
        if ($buyResult) {
            Write-Host "  Kaufstatus (Buy status): $($buyResult.success) - Sehr schoen!"
            Write-Host "  Nachricht (Message): $($buyResult.message) - Eine informative Mitteilung!"
            Write-Host "  Gesamtkosten (Total cost): $($buyResult.total_cost) - Ein fairer Preis, oder?"
            Write-Host "  Neuer Batteriestand (New battery level): $($buyResult.new_battery_level)% - Aufgeladen und bereit!"
        }
        
        # Check battery level after buying
        Start-Sleep -Seconds 1  # Wait a moment for the database to update
        $batteryAfterBuy = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
        if ($batteryAfterBuy) {
            Write-Host "`n  Batteriestand nach dem Kauf (Battery level after buying): $($batteryAfterBuy.level)% - Mehr Energie fuer Professor Alberto!"
            Write-Host "  Energie nach dem Kauf (Energy after buying): $($batteryAfterBuy.capacity.used) kWh - Jetzt haben wir Power!"
        }
        
        # Test selling electricity
        Write-Host "`n  Stromverkauf wird getestet (Testing selling electricity - Selling with German business acumen!):" -ForegroundColor Yellow
        Write-Host "  Endpoint: /trades/sell" -ForegroundColor Gray
        $sellRequest = @{
            quantity = 5.0  # Sell 5 kWh
            price = 45.0    # Set a specific price
        }
        Write-Host "  Request data: quantity = $($sellRequest.quantity) kWh, price = $($sellRequest.price)" -ForegroundColor Gray
        $sellResult = Invoke-ApiCall -Method "POST" -Endpoint "/trades/sell" -Body $sellRequest -Token $token
        if ($sellResult) {
            Write-Host "  Verkaufsstatus (Sell status): $($sellResult.success) - Genau nach Plan!"
            Write-Host "  Nachricht (Message): $($sellResult.message) - Vielen Dank fuer die Information!"
            Write-Host "  Gesamteinnahmen (Total revenue): $($sellResult.total_revenue) - Klingelt in der Kasse!"
            Write-Host "  Neuer Batteriestand (New battery level): $($sellResult.new_battery_level)% - Etwas leichter jetzt!"
        }
        
        # Check battery level after selling
        Start-Sleep -Seconds 1  # Wait a moment for the database to update
        $batteryAfterSell = Invoke-ApiCall -Method "GET" -Endpoint "/battery/status" -Token $token
        if ($batteryAfterSell) {
            Write-Host "`n  Batteriestand nach dem Verkauf (Battery level after selling): $($batteryAfterSell.level)% - Balance ist wichtig!"
            Write-Host "  Energie nach dem Verkauf (Energy after selling): $($batteryAfterSell.capacity.used) kWh - Perfekt ausbalanciert!"
        }
        
        # Test trade history endpoint
        Write-Host "`n  Handelshistorie wird ueberprueft (Checking trade history - A look into the past!):" -ForegroundColor Yellow
        Write-Host "  Endpoint: /trades/" -ForegroundColor Gray
        $tradeHistory = Invoke-ApiCall -Method "GET" -Endpoint "/trades/" -Token $token
        if ($tradeHistory) {
            Write-Host "  $($tradeHistory.Count) Handelsaufzeichnungen abgerufen (trade records retrieved) - Ordnung muss sein!"
            if ($tradeHistory.Count -gt 0) {
                Write-Host "  Letzter Handel (Latest trade): Typ: $($tradeHistory[0].type), Menge: $($tradeHistory[0].quantity), Preis: $($tradeHistory[0].price), Status: $($tradeHistory[0].status) - Professor Alberto wuerde den Handel genehmigen!"
            }
        }
    }

    # Trade History - Get trade history for user
    try {
        Write-Host "`nHandelshistorie wird ueberprueft... (Checking trade history - For accounting and Professor Alberto!)" -ForegroundColor Yellow
        Write-Host "Endpoint: /trades/" -ForegroundColor Gray
        $response = Invoke-ApiCall -Method "GET" -Endpoint "/trades/" -Token $token
        
        if ($response.Count -gt 0) {
            $latestTrade = $response[0]
            Write-Host "Handelshistorie abgerufen! (Trade history retrieved!) $($response.Count) Handelsaufzeichnungen gefunden. Super!" -ForegroundColor Green
            Write-Host "Letzter Handel (Latest trade) - Typ: $($latestTrade.type), Menge: $($latestTrade.quantity) kWh, Preis: $($latestTrade.price), Status: $($latestTrade.status) - Sehr professionell!" -ForegroundColor Green
        } else {
            Write-Host "Keine Handelsaufzeichnungen gefunden. (No trade records found) Vielleicht Zeit fuer den ersten Handel? Mach Professor Alberto stolz!" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Fehler beim Abrufen der Handelshistorie (Error retrieving trade history): $_ - Das haette nicht passieren sollen!" -ForegroundColor Red
    }

    # Trade Profit/Loss - Calculate profit/loss from executed trades
    try {
        Write-Host "`nGewinn/Verlust-Berechnung laeuft... (Running profit/loss calculation - Numbers that Professor Alberto will love!)" -ForegroundColor Yellow
        Write-Host "Endpoint: /performance/trade-pnl" -ForegroundColor Gray
        $response = Invoke-ApiCall -Method "GET" -Endpoint "/performance/trade-pnl" -Token $token
        
        Write-Host "Gewinn/Verlust-Berechnung abgerufen! (Trade P&L calculation retrieved!) Ausgezeichnet!" -ForegroundColor Green
        Write-Host "Zeitraum (Period): $($response.period.start_date) bis $($response.period.end_date) - Ein guter Betrachtungszeitraum!" -ForegroundColor Green
        Write-Host "Handel (Trades): $($response.trades.executed) ausgefuehrt von $($response.trades.total) insgesamt - Effizienz ist der Schluessel!" -ForegroundColor Green
        Write-Host "Volumen (Volume) - Kauf: $($response.volume.buy) kWh, Verkauf: $($response.volume.sell) kWh, Netto: $($response.volume.net) kWh - Deutsche Gruendlichkeit!" -ForegroundColor Green
        Write-Host "Finanzen (Financials - Professor Alberto's favorite part!):" -ForegroundColor Green
        Write-Host "  - Kaufkosten (Buy cost): $($response.financials.buy_cost) - Investitionen in die Zukunft!" -ForegroundColor Green
        Write-Host "  - Verkaufseinnahmen (Sell revenue): $($response.financials.sell_revenue) - Der Ertrag unserer Arbeit!" -ForegroundColor Green
        Write-Host "  - Gewinn/Verlust (Profit/Loss): $($response.financials.profit_loss) - Hoffentlich im Plus!" -ForegroundColor Green
        Write-Host "  - Gewinn/Verlust pro kWh (Profit/Loss per kWh): $($response.financials.profit_loss_per_kWh) - Die wichtigste Kennzahl!" -ForegroundColor Green
    } catch {
        Write-Host "Fehler beim Abrufen des Gewinn/Verlusts (Error retrieving profit/loss): $_ - Das ist ungluecklich!" -ForegroundColor Red
    }
}
else {
    Write-Host "Authentifizierung fehlgeschlagen (Authentication failed) - Das ist ein Problem!" -ForegroundColor Red
}

Write-Host "`nAPI-Test abgeschlossen - Alles fuer Professor Alberto bereit! (API test completed - Everything ready for Professor Alberto!)" -ForegroundColor Cyan
Write-Host "Vielen Dank fuer die Nutzung des Energiehandelsplattform-Tests. Auf Wiedersehen! (Thank you for using the Energy Trading Platform Test. Goodbye!)" -ForegroundColor Cyan