import json
import pandas as pd
import matplotlib.pyplot as plt


def analyze_battle_results(file_path="battle_results.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Błąd: Plik {file_path} nie został znaleziony.")
        return
    except json.JSONDecodeError:
        print(f"Błąd: Plik {file_path} nie zawiera poprawnego formatu JSON.")
        return

    if not data:
        print("Brak danych do analizy.")
        return

    df = pd.DataFrame(data)

    # Konwersja timestamp na datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    print("=" * 60)
    print(f"RAPORT ANALIZY BITEW ({len(df)} symulacji)")
    print("=" * 60)

    # 1. Ogólne statystyki zwycięstw
    print("\n--- ZWYCIĘZCY (OGÓŁEM) ---")
    win_counts = df["winner"].value_counts()
    for winner, count in win_counts.items():
        percentage = (count / len(df)) * 100
        print(f"{winner}: {count} ({percentage:.1f}%)")

    # 2. Najpopularniejsze scenariusze
    print("\n--- NAJPOPULARNIEJSZE SCENARIUSZE ---")
    scenario_counts = df["scenario_name"].value_counts()
    print(scenario_counts.to_string())

    # 3. Analiza strat (Śmiertelność)
    # Obliczamy początkową liczbę jednostek dla każdego wiersza
    def calculate_initial_total(row):
        return sum(row["initial_units"].values())

    df["initial_total"] = df.apply(calculate_initial_total, axis=1)
    df["casualty_rate"] = (1 - (df["survivors"] / df["initial_total"])) * 100

    avg_casualty = df["casualty_rate"].mean()
    print("\n--- ŚREDNIA ŚMIERTELNOŚĆ ---")
    print(f"Średnio w bitwie ginie {avg_casualty:.1f}% jednostek.")

    # 4. Szczegółowa analiza per scenariusz
    print("\n--- BALANS SCENARIUSZY ---")
    scenarios = df["scenario_name"].unique()

    for scenario in scenarios:
        subset = df[df["scenario_name"] == scenario]
        total_runs = len(subset)
        if total_runs == 0:
            continue

        print(f"\n> {scenario} (Rozegrano: {total_runs})")

        # Kto wygrywa w tym scenariuszu?
        scenario_wins = subset["winner"].value_counts()
        for winner, count in scenario_wins.items():
            pct = (count / total_runs) * 100
            print(f"  - {winner}: {pct:.1f}%")

        # Średnia liczba ocalałych
        avg_survivors = subset["survivors"].mean()
        print(f"  - Średnio ocalałych: {avg_survivors:.1f}")

    # Opcjonalnie: Wykresy
    try:
        # 1. Wykres ogólny zwycięstw
        plt.figure(figsize=(10, 6))
        win_counts.plot(kind="bar", color=["skyblue", "salmon", "lightgray"])
        plt.title("Rozkład zwycięstw w symulacjach")
        plt.xlabel("Strona konfliktu")
        plt.ylabel("Liczba zwycięstw")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig("win_stats.png")
        print("\n[INFO] Wygenerowano wykres 'win_stats.png'")

        # 2. Wykres balansu scenariuszy (Stacked Bar Chart)
        # Pivot table: wiersze=scenariusz, kolumny=zwycięzca, wartości=liczba
        pivot_df = df.pivot_table(
            index="scenario_name", columns="winner", aggfunc="size", fill_value=0
        )

        # Normalizacja do 100%
        pivot_pct = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100

        ax = pivot_pct.plot(
            kind="barh", stacked=True, figsize=(12, 8), colormap="coolwarm"
        )
        plt.title("Balans Scenariuszy (Procent Zwycięstw)")
        plt.xlabel("Procent (%)")
        plt.ylabel("Scenariusz")
        plt.legend(title="Zwycięzca", bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.tight_layout()
        plt.savefig("scenario_balance.png")
        print("[INFO] Wygenerowano wykres 'scenario_balance.png'")

        # 3. Wykres śmiertelności (Boxplot)
        plt.figure(figsize=(12, 8))
        df.boxplot(column="casualty_rate", by="scenario_name", grid=False, vert=False)
        plt.title("Rozkład śmiertelności w scenariuszach")
        plt.suptitle("")  # Usuwa automatyczny tytuł pandas
        plt.xlabel("Śmiertelność (%)")
        plt.ylabel("Scenariusz")
        plt.tight_layout()
        plt.savefig("casualty_stats.png")
        print("[INFO] Wygenerowano wykres 'casualty_stats.png'")

    except Exception as e:
        print(f"\n[INFO] Nie udało się wygenerować wykresów: {e}")


if __name__ == "__main__":
    analyze_battle_results()
