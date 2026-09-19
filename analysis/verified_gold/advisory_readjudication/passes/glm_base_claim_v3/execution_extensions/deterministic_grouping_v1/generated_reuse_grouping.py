async def reuse_grouping(plan, members, args, sem, out, pass_hash, categories=None):
    """File-grouped existing workflow, with interval-prioritized candidates."""
    units = plan['units']; url = plan['url']; key = pr_key(url)
    async def group(order, phase):
        if len(order) < 2: return [order] if order else []
        shown = [classifier_candidate(members[units[i]['representative']]['record']) for i in order]
        body = '\n'.join(f'{j}. {t}' for j,t in enumerate(shown))
        prompt = GROUP_PROMPT.format(reps=body)
        if len(prompt)>GROUP_CONTEXT_LIMIT: raise ValueError('Explicit grouping context limit exceeded')
        req = {'url':url, 'model':args.group_judge, 'system':GROUP_SYSTEM, 'prompt':prompt,
               'effort':args.effort,'max_tokens':8192,'units':order}
        sha=digest(req); path=out/'grouping_calls'/key/f'{phase}_{sha[:16]}.json'
        if path.exists():
            saved=json.loads(path.read_text())
            if saved['pass_digest']!=pass_hash or saved['request_sha256']!=sha: raise ValueError('Stale grouping request')
            if saved['status']=='complete': return constrained_groups([[order[i] for i in g] for g in validate_group_mapping(saved['parsed_response'],len(order))],units)
        for attempt in range(3):
            parsed=usage=None; error=None; start=time.time()
            try:
                async with sem:
                    if (out/'STOP').exists(): raise DrainRequested()
                    parsed,tin,tout,usage=await model_router.call_model_json(args.group_judge,GROUP_SYSTEM,prompt,effort=args.effort,max_tokens=8192)
                mapping=validate_group_mapping(parsed,len(order))
            except DrainRequested: raise
            except Exception as exc: error=type(exc).__name__
            saved={'url':url,'pass_digest':pass_hash,'request_sha256':sha,'request':req,'parsed_response':parsed,
                   'per_model_usage':usage,'status':'error' if error else 'complete','error_type':error,'elapsed_s':time.time()-start}
            write_json(out/'grouping_attempts'/key/f'{phase}_{time.time_ns()}.json',saved);write_json(path,saved)
            write_progress(out,pass_hash,'grouping',event=f'{url} {phase}: {error or "complete"}')
            if not error:
                result=constrained_groups([[order[i] for i in g] for g in mapping],units)
                print(f'{url} {phase}: {len(order)} -> {len(result)}',flush=True);return result
        raise RuntimeError(f'{url} {phase}: grouping remains incomplete after three attempts')
    checkpoint = out/'proposal_checkpoints'/f'{key}.json'
    binding = proposal_binding(plan, members, pass_hash, categories)
    proposed = load_proposal(checkpoint, binding, len(units))
    if proposed is None:
        buckets=defaultdict(list)
        old_files=defaultdict(set)
        for u in units:
            if u['location'][0]:
                for old in u['old_groups']:old_files[old].add(u['location'][0])
        candidate_edges=[]
        bucket_for={}
        for i,u in enumerate(units):
            if u['defect_ids']:continue
            # A missing location is not a match. An existing semantic group with one
            # validated file supplies only a candidate bucket for fresh confirmation.
            linked={f for old in u['old_groups'] for f in old_files[old]}
            bucket=u['location'][0] or (next(iter(linked)) if len(linked)==1 else 'unknown')
            bucket=((categories or {}).get(i,'unclassified'),bucket)
            buckets[bucket].append(i);bucket_for[i]=bucket
        for file,indices in buckets.items():
            for n,i in enumerate(indices):
                for j in indices[n+1:]:
                    if intervals_overlap(units[i]['location'],units[j]['location']):
                        candidate_edges.append({'units':[i,j],'reason':'same-file overlapping intervals'})
        write_json(out/'candidates'/f'{key}.json',{'url':url,'pass_digest':pass_hash,
            'bucket_for':bucket_for,'interval_edges':candidate_edges,
            'policy':'candidate priority only; no automatic identity union; unknown requires semantic confirmation'})
        adjacency=defaultdict(set)
        for edge in candidate_edges:
            i,j=edge['units'];adjacency[i].add(j);adjacency[j].add(i)
        components={};seen=set()
        for i in range(len(units)):
            if i in seen:continue
            todo=[i];component=[]
            while todo:
                j=todo.pop()
                if j in seen:continue
                seen.add(j);component.append(j);todo.extend(adjacency[j]-seen)
            for j in component:components[j]=min(component)
        jobs=[]
        for file,indices in sorted(buckets.items()):
            order=sorted(indices,key=lambda i:(components[i],units[i]['location'][1] if units[i]['location'][1] is not None else 10**9, units[i]['old_groups'], classifier_candidate(members[units[i]['representative']]['record'])))
            for start in range(0,len(order),GROUP_CHUNK): jobs.append((file,order[start:start+GROUP_CHUNK],f'{digest(file)[:10]}_{start//GROUP_CHUNK:03}'))
        queue=asyncio.Queue();results=[]
        for job in jobs:queue.put_nowait(job)
        errors=[]
        async def worker():
            while not queue.empty() and not errors and not (out/'STOP').exists():
                file,order,name=queue.get_nowait()
                try: results.append((file,name,await group(order,name)))
                except Exception as exc: errors.append(exc)
                finally:queue.task_done()
        await asyncio.gather(*(worker() for _ in range(args.concurrency)))
        if errors:raise errors[0]
        if not queue.empty() or (out/'STOP').exists():raise DrainRequested()
        byfile=defaultdict(list)
        for file,name,groups in stable_results(results):byfile[file].extend(groups)
        final=[[i] for i,u in enumerate(units) if u['defect_ids']]
        for file,groups in sorted(byfile.items()):
            reps=[min(g,key=lambda i:len(classifier_candidate(members[units[i]['representative']]['record']))) for g in groups]
            owner={rep:g for rep,g in zip(reps,groups)}
            merged=await group(reps,f'{digest(file)[:10]}_merge') if len(groups)>1 else [reps]
            final.extend([[i for rep in g for i in owner[rep]] for g in merged])
        proposed=final
        freeze_proposal(checkpoint, binding, proposed, len(units))
    from tools import advisory_pair_validation as pv
    async def compare_pairs(pairs):
        results={};queue=asyncio.Queue();errors=[]
        for start in range(0,len(pairs),20):queue.put_nowait((start,pairs[start:start+20]))
        async def worker():
            while not queue.empty() and not errors and not (out/'STOP').exists():
                start,chunk=queue.get_nowait()
                texts=[(classifier_candidate(members[units[a]['representative']]['record']),classifier_candidate(members[units[b]['representative']]['record'])) for a,b in chunk]
                req={'url':url,'model':args.group_judge,'system':pv.SYSTEM,'prompt':pv.make_prompt(texts),'effort':args.effort,'pairs':chunk}
                sha=digest(req);path=out/'pair_calls'/key/f'{sha}.json'
                try:
                    if path.exists():
                        saved=json.loads(path.read_text())
                        if saved['pass_digest']!=pass_hash:raise ValueError('Stale pair checkpoint')
                        if saved['status']=='complete':
                            results[start]=pv.parse_votes(saved['parsed_response'],len(chunk));continue
                    for attempt in range(3):
                        parsed=usage=None;error=None;began=time.time()
                        try:
                            async with sem:
                                if (out/'STOP').exists():raise DrainRequested()
                                parsed,tin,tout,usage=await model_router.call_model_json(args.group_judge,pv.SYSTEM,req['prompt'],effort=args.effort,max_tokens=8192)
                            votes=pv.parse_votes(parsed,len(chunk))
                        except DrainRequested:raise
                        except Exception as exc:error=type(exc).__name__
                        saved={'url':url,'pass_digest':pass_hash,'request_sha256':sha,'request':req,'parsed_response':parsed,'usage':usage,'status':'error' if error else 'complete','error_type':error,'elapsed_s':time.time()-began}
                        write_json(out/'pair_attempts'/key/f'{sha}_{time.time_ns()}.json',saved);write_json(path,saved)
                        write_progress(out,pass_hash,'pair_validation',event=f'{url}: {len(chunk)} pairs {error or chr(111)+chr(107)}')
                        if not error:
                            results[start]=votes;break
                    else:raise RuntimeError('Pair validation incomplete after retries')
                except Exception as exc:errors.append(exc)
                finally:queue.task_done()
        await asyncio.gather(*(worker() for _ in range(args.concurrency)))
        if errors:raise errors[0]
        if not queue.empty() or (out/'STOP').exists():raise DrainRequested()
        return [vote for start in sorted(results) for vote in results[start]]
    final=await pv.refine_groups(proposed,compare_pairs)
    # Classification identities are exact case-preserving claims (or each
    # member's own fixed D assignment). Semantic identity NEVER shares verdicts.
    cids=[None]*len(members);duplicate_cids=[None]*len(members);representatives={};sources={}
    for cid,unit in enumerate(units):
        representatives[cid]=unit['representative']
        sources[cid]={'defect_ids':unit['defect_ids'],'units':[cid]}
        for member in unit['members']:cids[member]=cid
    for duplicate_id,group in enumerate(final):
        for unit in group:
            for member in units[unit]['members']:duplicate_cids[member]=duplicate_id
    if any(c is None for c in cids+duplicate_cids):raise ValueError('Missing final membership')
    write_json(out/'dedup_audit'/f'{key}.json',{'url':url,'pass_digest':pass_hash,'proposed_groups':proposed,'validated_groups':final,
        'high_multiplicity_groups':[g for g in final if len(g)>=10],
        'method':'full-text material-equivalence pair validation, recursive rejects, all-pairs clique gate; independent exact-claim verdicts'})
    return {'url':url,'pass_digest':pass_hash,'membership_sha256':digest(members),'cids':cids,'duplicate_cids':duplicate_cids,'representatives':representatives,'sources':sources}
