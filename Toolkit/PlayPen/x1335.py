import math
import sys
import copy

def get_ccs(xscale_lp):

    ccs = { }

    file_names = { }

    xmax = 0

    records = open(xscale_lp).readlines()

    # first scan through to get the file names...

    for j, record in enumerate(records):
        if 'NUMBER OF UNIQUE REFLECTIONS' in record:

            k = j + 5

            while len(records[k].split()) == 5:
                values = records[k].split()
                file_names[int(values[0])] = values[-1]

                k += 1

            break

    if not file_names:
        for j, record in enumerate(records):
            if 'SET# INTENSITY  ACCEPTED REJECTED' in record:
                
                k = j + 1
                
                while len(records[k].split()) == 5:
                    values = records[k].split()
                    file_names[int(values[0])] = values[-1]
                    
                    k += 1
                    
                break


    for j, record in enumerate(records):

        if 'CORRELATIONS BETWEEN INPUT DATA SETS' in record:

            k = j + 5

            while len(records[k].split()) == 6:
                values = records[k].split()

                _i = int(values[0])
                _j = int(values[1])
                _n = int(values[2])
                _cc = float(values[3])

                ccs[(_i, _j)] = (_n, _cc)
                ccs[(_j, _i)] = (_n, _cc)

                xmax = _i + 1

                k += 1

            break

    for j in range(xmax):
        ccs[(j + 1, j + 1)] = (0, 0)
        print '%4d %6.4f %s' % (j + 1,
                                sum([ccs[(i + 1, j + 1)][1]
                                     for i in range(xmax)]) / (xmax - 1),
                                file_names[j + 1])

def ccs_to_R(xscale_lp):

    ccs = { }

    file_names = { }

    xmax = 0

    records = open(xscale_lp).readlines()

    # first scan through to get the file names...

    for j, record in enumerate(records):
        if 'NUMBER OF UNIQUE REFLECTIONS' in record:

            k = j + 5

            while len(records[k].split()) == 5:
                values = records[k].split()
                file_names[int(values[0])] = values[-1]

                k += 1

            break

    if not file_names:
        for j, record in enumerate(records):
            if 'SET# INTENSITY  ACCEPTED REJECTED' in record:
                
                k = j + 1
                
                while len(records[k].split()) == 5:
                    values = records[k].split()
                    file_names[int(values[0])] = values[-1]
                    
                    k += 1
                    
                break


    for j, record in enumerate(records):

        if 'CORRELATIONS BETWEEN INPUT DATA SETS' in record:

            k = j + 5

            while len(records[k].split()) == 6:
                values = records[k].split()

                _i = int(values[0])
                _j = int(values[1])
                _n = int(values[2])
                _cc = float(values[3])

                ccs[(_i, _j)] = (_n, _cc)
                ccs[(_j, _i)] = (_n, _cc)

                xmax = _i + 1

                k += 1

            break

    tokens = []

    distances = {}
    
    for j in range(xmax):
        for i in range(xmax):
            cc = ccs.get((i + 1, j + 1), (0, 1.0))[1]
            if cc < 0.01:
                cc = 0.01
            tokens.append(((1.0 / cc) - 1))
            distances[(i, j)] = (1.0 / cc) - 1

    fout = open('x1335.R', 'w')
    fout.write('m = matrix(c(')
    for t in tokens[:-1]:
        fout.write('%.4f, ' % t)
    fout.write('%f), nrow = %d)\n' % (tokens[-1], xmax))
    fout.write('d = as.dist(m)\n')
    fout.write('c = hclust(d, method = "ward")\n')
    fout.write('plot(c)\n')

    # try implementing a "toy" ward linkage...

    spaces = []

    for key in distances:
        spaces.append((distances[key], key))

    spaces.sort()

    fout = open('x1335.S', 'w')
    for s in spaces:
        fout.write('%f\n' % s[0])
    fout.close()
    
    dmax = 0.01

    sets = []
    
    for s in spaces:
        if s[0] > dmax:
            break

        i, j = s[1]

        for _s in sets:

            if i in _s and j in _s:
                continue
            
            if i in _s:
                _s.add(j)
                continue

            if j in _s:
                _s.add(i)
                continue
                
        sets.append(set([i, j]))

    for _s in sorted(sets):
        # print _s
        pass


if __name__ == '__main__':

    get_ccs(sys.argv[1])
    ccs_to_R(sys.argv[1])
    