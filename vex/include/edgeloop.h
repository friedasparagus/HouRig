#ifndef __edgeloop__
#define __edgeloop__

function int
pt_shares_prim(int a; int b){
    int result = -1;
    
    foreach(int prim; pointprims(0, a)){
        if(find(pointprims(0, b), prim) > -1)
            result = 1;
    }
    
    return result;
}

function int[]
edgeloop(int a; int b; int closed; int maxiters){
    int __maxiters__ = maxiters;

    int flag = 1;
    
    int last = a;
    int cur = b;

    // if the two given points are not adjacent, exit
    if(find(neighbours(0, last), cur) < 0)
      return {};

    int result[] = {};
    
    append(result, last);
    append(result, cur);

    int itercount = 0;
    
    while(flag){
        if(itercount > __maxiters__)
            return {};

        itercount += 1;

        if(cur == a)
          return result;

        flag = 0;
        
        int n_arr[] = neighbours(0, cur);

        if(len(pointprims(0, cur)) != 4)
          return result;

        foreach(int ne; n_arr){

            if(ne != last && pt_shares_prim(last, ne) < 0){
                last = cur;
                cur = ne;

                if(cur == a){
                  closed = 1;
                  return result;
                }

                append(result, cur);
                flag = 1;
            }
        }
    }

    return result;
}

function int[]
edgeloop(int a; int b; int maxiters; int returnclosed; string breakattrs[]; int closed; int hitattr){
    int __maxiters__ = maxiters;

    int flag = 1;
    
    int last = a;
    int cur = b;

    // if the two given points are not adjacent, exit
    if(find(neighbours(0, last), cur) < 0)
      return {};

    int result[] = {};
    
    append(result, last);
    append(result, cur);

    int itercount = 0;
    closed = 0;
    
    while(flag){
        if(itercount > __maxiters__)
            return {};

        itercount += 1;

        if(cur == a)
          return result;

        flag = 0;
        
        int n_arr[] = neighbours(0, cur);

        if(len(pointprims(0, cur)) != 4){
          return result;
        }

        foreach(int ne; n_arr){

            if(ne != last && pt_shares_prim(last, ne) < 0){
                last = cur;
                cur = ne;

                if(cur == a){
                  closed = 1;
                  if(returnclosed)
                    return result;
                  else
                    return {};
                }

                foreach(string attr; breakattrs)
                {
                    if(point(0, attr, cur) > 0){
                        hitattr = 1;
                        return result;
                    }
                }

                append(result, cur);
                flag = 1;
            }
        }
    }

    return result;
}

# endif
