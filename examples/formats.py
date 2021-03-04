from conffu import Config

cfg = Config.load('example.json')

print(cfg.objects[0])
cfg.globals['amount'] = 5
# substitution happens when you access the config
print(cfg.objects[0])

cfg.save('example.xml')
