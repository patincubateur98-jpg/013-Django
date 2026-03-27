from pathlib import Path
import sqlite3

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academics.models import Classe, Cours, Etudiant, Tuteur
from imports.models import ImportLog


class Command(BaseCommand):
	help = "Importe classes, cours, tuteurs et étudiants depuis une base SQLite Flask."

	def add_arguments(self, parser):
		parser.add_argument(
			"--source",
			required=True,
			help="Chemin vers la base SQLite source (ex: D:/chemin/pcnc.db)",
		)
		parser.add_argument(
			"--dry-run",
			action="store_true",
			help="Prévisualise l'import sans écrire en base Django.",
		)

	def handle(self, *args, **options):
		source = Path(options["source"])
		dry_run = options["dry_run"]

		if not source.exists():
			raise CommandError(f"Fichier source introuvable: {source}")

		conn = sqlite3.connect(source)
		conn.row_factory = sqlite3.Row

		try:
			available_tables = self._get_tables(conn)
			required = {"classe", "cours", "tuteur", "etudiant"}
			missing = sorted(required - available_tables)
			if missing:
				raise CommandError(
					"Tables manquantes dans la base source: " + ", ".join(missing)
				)

			stats = {
				"classe": 0,
				"cours": 0,
				"tuteur": 0,
				"etudiant": 0,
				"total": 0,
			}

			if dry_run:
				self._simulate_import(conn, stats)
				self.stdout.write(self.style.WARNING("Mode dry-run: aucune écriture effectuée."))
			else:
				with transaction.atomic():
					self._import_table(conn, "classe", Classe, ["id", "numero", "nom", "archived"], stats)
					self._import_table(conn, "cours", Cours, ["id", "code", "nom"], stats)
					self._import_table(
						conn,
						"tuteur",
						Tuteur,
						[
							"id",
							"genre",
							"nom",
							"prenom",
							"telephone",
							"email",
							"role",
							"username",
							"password_hash",
							"is_active",
							"classe_affectee",
						],
						stats,
					)
					self._import_table(
						conn,
						"etudiant",
						Etudiant,
						[
							"id",
							"genre",
							"nom",
							"prenom",
							"email",
							"telephone",
							"presence",
							"classe_id",
							"cours_id",
							"tuteur_id",
						],
						stats,
					)

					ImportLog.objects.create(
						fichier=str(source),
						statut="SUCCES",
						lignes_total=stats["total"],
						lignes_ajoutees=stats["total"],
						lignes_doublons=0,
						lignes_erreurs=0,
						details=(
							f"Classe={stats['classe']}, Cours={stats['cours']}, "
							f"Tuteur={stats['tuteur']}, Etudiant={stats['etudiant']}"
						),
					)

			self.stdout.write(self.style.SUCCESS("Import terminé."))
			self.stdout.write(
				f"Classes: {stats['classe']} | Cours: {stats['cours']} | "
				f"Tuteurs: {stats['tuteur']} | Étudiants: {stats['etudiant']}"
			)
		finally:
			conn.close()

	@staticmethod
	def _get_tables(conn):
		cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
		return {row[0] for row in cur.fetchall()}

	def _simulate_import(self, conn, stats):
		for table_name in ["classe", "cours", "tuteur", "etudiant"]:
			count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
			stats[table_name] = count
			stats["total"] += count

	def _import_table(self, conn, table_name, model, allowed_columns, stats):
		rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
		for row in rows:
			payload = {}
			for col in allowed_columns:
				if col in row.keys():
					payload[col] = row[col]

			row_id = payload.pop("id", None)
			if row_id is None:
				model.objects.create(**payload)
			else:
				model.objects.update_or_create(id=row_id, defaults=payload)

			stats[table_name] += 1
			stats["total"] += 1