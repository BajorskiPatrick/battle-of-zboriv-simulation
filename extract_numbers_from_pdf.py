#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do wyciągania akapitów zawierających liczby z PDF
Bitwa pod Zborowem - W. Kucharski
"""

import re
import sys

try:
    import pdfplumber
except ImportError:
    print("=" * 80)
    print("BŁĄD: Brak biblioteki pdfplumber")
    print("=" * 80)
    print("\nAby zainstalować, uruchom:")
    print("  pip install pdfplumber")
    print("\nlub jeśli używasz venv:")
    print("  source venv/bin/activate  # Linux/Mac")
    print("  venv\\Scripts\\activate     # Windows")
    print("  pip install pdfplumber")
    print("\nNastępnie uruchom ponownie ten skrypt.")
    sys.exit(1)

def extract_number_contexts(pdf_path, context_chars=50):
    """
    Wyciąga kontekst wokół liczb z pliku PDF (np. 50 znaków przed i po).
    """
    number_contexts = []
    
    print(f"Wczytywanie pliku: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Znaleziono {total_pages} stron\n")
            
            for page_num, page in enumerate(pdf.pages, 1):
                # Wyciągnij tekst ze strony
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Szukaj wszystkich liczb w tekście
                # Wzorce: liczby 3+ cyfr, liczby z jednostkami (tys., tysiąc, etc.)
                patterns = [
                    (r'\d{3,}', 'large_number'),  # Liczby 3+ cyfr
                    (r'\d+\s*(tys\.|tysięcy|tys\.?|żołnierzy|jazdy|piechoty|dragoni|kozak|tatar|jednostek|oddział)', 'military_number'),  # Liczby wojskowe
                    (r'\d+\s*%', 'percentage'),  # Procenty
                ]
                
                for pattern, pattern_type in patterns:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        number = match.group()
                        start_pos = match.start()
                        end_pos = match.end()
                        
                        # Wyciągnij kontekst (50 znaków przed i po)
                        context_start = max(0, start_pos - context_chars)
                        context_end = min(len(text), end_pos + context_chars)
                        context = text[context_start:context_end]
                        
                        # Sprawdź czy kontekst zawiera słowa kluczowe związane z wojskiem
                        military_keywords = [
                            'żołnierz', 'wojsko', 'armia', 'koronna', 'kozacy', 'tatar',
                            'piechota', 'jazda', 'dragonia', 'ruszenie', 'oddział',
                            'jednostka', 'sztandar', 'chorągiew', 'pułk', 'regiment',
                            'zborów', 'zborowem', 'bitwa', 'starcie', 'walka', 'król',
                            'jan kazimierz', 'chmielnicki', 'chan', 'tatarski'
                        ]
                        
                        context_lower = context.lower()
                        has_military_context = any(keyword in context_lower for keyword in military_keywords)
                        
                        # Dodaj jeśli to duża liczba (3+ cyfry) lub ma kontekst wojskowy
                        if pattern_type == 'large_number' or has_military_context:
                            # Oznacz liczbę w kontekście
                            marked_context = context[:start_pos - context_start] + \
                                           f" >>>{number}<<< " + \
                                           context[end_pos - context_start:]
                            
                            number_contexts.append({
                                'page': page_num,
                                'number': number,
                                'type': pattern_type,
                                'context': marked_context.strip(),
                                'has_military_context': has_military_context
                            })
    
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {pdf_path}")
        return []
    except Exception as e:
        print(f"Błąd podczas przetwarzania PDF: {e}")
        return []
    
    return number_contexts

def main():
    pdf_path = "W_Kucharski_Bitwa_pod_Zborowem.pdf"
    context_chars = 50  # Liczba znaków przed i po liczbie
    
    print("=" * 80)
    print("WYCIĄGANIE KONTEKSTU WOKÓŁ LICZB Z PDF")
    print("Bitwa pod Zborowem - W. Kucharski")
    print(f"Kontekst: {context_chars} znaków przed i po każdej liczbie")
    print("=" * 80)
    print()
    
    contexts = extract_number_contexts(pdf_path, context_chars)
    
    if not contexts:
        print("Nie znaleziono liczb z kontekstem.")
        return
    
    print(f"\nZnaleziono {len(contexts)} wystąpień liczb:\n")
    print("=" * 80)
    
    # Grupuj po stronach
    current_page = 0
    for item in contexts:
        if item['page'] != current_page:
            current_page = item['page']
            print(f"\n{'='*80}")
            print(f"STRONA {current_page}")
            print('='*80)
        
        print(f"\n[Strona {item['page']}] Liczba: {item['number']} (typ: {item['type']})")
        if item['has_military_context']:
            print("✓ Kontekst wojskowy")
        print("-" * 80)
        print(item['context'])
        print()
    
    # Podsumowanie
    print("\n" + "=" * 80)
    print("PODSUMOWANIE")
    print("=" * 80)
    print(f"Łącznie znaleziono: {len(contexts)} wystąpień liczb")
    print(f"Na {len(set(c['page'] for c in contexts))} stronach")
    print(f"Z kontekstem wojskowym: {sum(1 for c in contexts if c['has_military_context'])}")
    
    # Zapisz do pliku
    output_file = "extracted_numbers.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("WYCIĄGNIĘTY KONTEKST WOKÓŁ LICZB Z PDF\n")
        f.write("Bitwa pod Zborowem - W. Kucharski\n")
        f.write(f"Kontekst: {context_chars} znaków przed i po każdej liczbie\n")
        f.write("=" * 80 + "\n\n")
        
        current_page = 0
        for item in contexts:
            if item['page'] != current_page:
                current_page = item['page']
                f.write(f"\n{'='*80}\n")
                f.write(f"STRONA {current_page}\n")
                f.write('='*80 + "\n")
            try:
                if float(item['number']) < 2000:
                    continue
                
            except ValueError:
                pass
            f.write(f"\n[Strona {item['page']}] Liczba: {item['number']} (typ: {item['type']})\n")
            if item['has_military_context']:
                f.write("✓ Kontekst wojskowy\n")
            f.write("-" * 80 + "\n")
            f.write(item['context'] + "\n\n")
    
    print(f"\nWyniki zapisano również do pliku: {output_file}")

if __name__ == "__main__":
    main()

