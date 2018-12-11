print('NOTE: scores may be entered as a space separated string or comma-separated string.')

p2p_score = input('Pix2pix score: ')
uresnet9_score = input('UResNet9 score: ')

if ',' in p2p_score:
    p2p_list = [int(x) for x in p2p_score.split(',')]
else:
    p2p_list = [int(x) for x in p2p_score.split(' ')]

if ',' in uresnet9_score:
    uresnet9_list = [int(x) for x in uresnet9_score.split(',')]
else:
    uresnet9_list = [int(x) for x in uresnet9_score.split(' ')]

# calculate sums
p2p_total = sum(p2p_list)
uresnet9_total = sum(uresnet9_list)

print('Pix2Pix total score: ' + str(p2p_total) + '/200; \tAverage per-image score: ' + str(int(round(p2p_total / 200 * 4))), end = '')
print('; Maximum score: ' + str(max(p2p_list)) + '; Minimum score: ' + str(min(p2p_list)))
print('UResNet9 total score: ' + str(uresnet9_total) + '/200; \tAverage per-image score: ' + str(int(round(uresnet9_total / 200 * 4))), end = '')
print('; Maximum score: ' + str(max(uresnet9_list)) + '; Minimum score: ' + str(min(uresnet9_list)))