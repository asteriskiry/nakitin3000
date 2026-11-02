# Nakitin3000
Nakittautumisjärjestelmä tapahtumajärjestejille. Live: <https://nakit.asteriski.fi>.

Author: [Janne Iltanen](https://github.com/jatail)

## Ohjeet kehitykseen
Tuotannon Docker-siirron ohjeet: [DEPLOYMENT.md](DEPLOYMENT.md).

The old Compose development setup has been replaced with a Gunicorn container.
Read [DEPLOYMENT.md](DEPLOYMENT.md) for required private configuration, testing,
database backup requirements and rollback. Do not start it against production
until the backup has been restored and staging has been verified.

Organization repository: https://github.com/asteriskiry/nakitin3000.
