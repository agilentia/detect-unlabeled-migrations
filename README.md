# Detect unlabeled migrations

Detects if a pr contains migrations but the migratios.uptime or migrations.downtime labels are missing.

## Usage in workflow

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run migration check action
        uses: agilentia/detect-unlabeled-migrations@main

        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          base_branch: 'master'
          required_labels: 'migrations.uptime, migrations.downtime'
          warning_label: 'Missing migration labels'
          slack_channel_id: 'DPXKM3429'

```

[additional info](https://docs.github.com/en/actions/sharing-automations/creating-actions/creating-a-composite-action)
