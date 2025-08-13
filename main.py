def carica_csv(file):
    """Carica e valida un file CSV"""
    try:
        # Leggi il contenuto del file come stringa
        content = file.read().decode('utf-8')
        lines = content.split('\n')
        
        # Trova l'inizio dei dati storici
        data_start_index = -1
        for i, line in enumerate(lines):
            if '=== DATI STORICI ===' in line:
                data_start_index = i + 1
                break
            # Se non troviamo il marker, cerchiamo la prima riga con formato data
            elif line.strip() and not line.startswith('===') and not line.startswith('Nome') and not line.startswith('Ticker') and not line.startswith('Data Download') and not line.startswith('Periodo') and not line.startswith('Numero') and not line.startswith('Performance') and not line.startswith('Prezzo') and not line.startswith('Deviazione') and ',' in line:
                # Controlla se sembra una riga di dati (inizia con una data)
                first_part = line.split(',')[0].strip()
                if first_part and (first_part.replace('-', '').replace('/', '').isdigit() or '/' in first_part or '-' in first_part):
                    data_start_index = i
                    break
        
        if data_start_index == -1:
            # Fallback: prova a leggere come CSV normale
            from io import StringIO
            df = pd.read_csv(StringIO(content))
        else:
            # Estrai solo le righe dei dati
            data_lines = lines[data_start_index:]
            
            # Rimuovi righe vuote
            data_lines = [line for line in data_lines if line.strip()]
            
            if not data_lines:
                return None, "Nessun dato trovato nel file"
            
            # Crea un nuovo CSV string con solo i dati
            csv_content = '\n'.join(data_lines)
            
            # Leggi come DataFrame
            df = pd.read_csv(StringIO(csv_content), header=None)
        
        # Pulisci i nomi delle colonne se presenti
        if hasattr(df.columns, 'str'):
            df.columns = [pulisci_nome_colonna(str(col)) for col in df.columns]
        
        # Verifica che abbia almeno 2 colonne
        if len(df.columns) < 2:
            return None, "Il file deve avere almeno 2 colonne (Data e Prezzo)"
        
        # Se il DataFrame non ha header, assegna nomi basati sul numero di colonne
        if df.columns[0] == 0:  # Significa che non c'erano header
            if len(df.columns) >= 4:
                df.columns = ['Date', 'Price', 'Performance_PCT', 'Performance_ABS'] + [f'Col_{i}' for i in range(4, len(df.columns))]
            else:
                df.columns = ['Date', 'Price'] + [f'Col_{i}' for i in range(2, len(df.columns))]
        else:
            # Rinomina le prime due colonne
            df.columns = ['Date', 'Price'] + list(df.columns[2:])
        
        # Converti la colonna Date
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Converti la colonna Price in numerico
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        # Rimuovi righe con valori mancanti nelle colonne essenziali
        df = df.dropna(subset=['Date', 'Price'])
        
        # Ordina per data
        df = df.sort_values('Date').reset_index(drop=True)
        
        if len(df) < 2:
            return None, "Il file deve contenere almeno 2 righe valide"
        
        return df, None
        
    except Exception as e:
        return None, f"Errore nel caricamento: {str(e)}"
