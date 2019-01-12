from deep_rl import *

def foo(game, **kwargs):
    kwargs.setdefault('tag', foo.__name__)
    kwargs.setdefault('log_dir', get_default_log_dir(kwargs['tag']))
    config = Config()
    config.merge(kwargs)

def batch():
    cf = Config()
    cf.add_argument('--i1', type=int, default=0)
    cf.add_argument('--i2', type=int, default=0)
    cf.merge()

    games = ['HalfCheetah-v2', 'Swimmer-v2', 'Hopper-v2', 'Walker2d-v2']
    game = games[cf.i1 % 4]
    algo = cf.i1 // 4
    if algo == 0:
        ucb_ddpg_continuous(game=game, run=cf.i2, remark='ucb')
    elif algo == 1:
        ddpg_continuous(game=game, run=cf.i2)

    exit()


def single_run(run, game, fn, tag, **kwargs):
    random_seed()
    log_dir = './log/dist_rl-%s/%s/%s-run-%d' % (game, fn.__name__, tag, run)
    fn(game=game, log_dir=log_dir, tag=tag, **kwargs)

def multi_runs(game, fn, tag, **kwargs):
    kwargs.setdefault('runs', 2)
    runs = kwargs['runs']
    if np.isscalar(runs):
        runs = np.arange(0, runs)
    kwargs.setdefault('parallel', False)
    if not kwargs['parallel']:
        for run in runs:
            single_run(run, game, fn, tag, **kwargs)
        return
    ps = [mp.Process(target=single_run, args=(run, game, fn, tag), kwargs=kwargs) for run in runs]
    for p in ps:
        p.start()
        time.sleep(1)
    for p in ps: p.join()

def ddpg_continuous(**kwargs):
    set_tag(kwargs)
    kwargs.setdefault('log_dir', get_default_log_dir(kwargs['tag']))
    kwargs.setdefault('gate', F.relu)
    kwargs.setdefault('weight_decay', 0)
    kwargs.setdefault('state_norm', False)
    config = Config()
    config.merge(kwargs)

    config.task_fn = lambda: Task(kwargs['game'])
    config.eval_env = Task(kwargs['game'], log_dir=kwargs['log_dir'])
    config.max_steps = int(2e6)
    config.eval_interval = int(1e4)
    config.eval_episodes = 20

    if kwargs['state_norm']:
        config.state_normalizer = MeanStdNormalizer()

    config.network_fn = lambda: DeterministicActorCriticNet(
        config.state_dim, config.action_dim,
        actor_body=FCBody(config.state_dim, (400, 300), gate=kwargs['gate']),
        critic_body=TwoLayerFCBodyWithAction(
            config.state_dim, config.action_dim, (400, 300), gate=kwargs['gate']),
        actor_opt_fn=lambda params: torch.optim.Adam(params, lr=1e-4),
        critic_opt_fn=lambda params: torch.optim.Adam(params, lr=1e-3, weight_decay=kwargs['weight_decay']))

    config.replay_fn = lambda: Replay(memory_size=int(1e6), batch_size=64)
    config.discount = 0.99
    config.random_process_fn = lambda: OrnsteinUhlenbeckProcess(
        size=(config.action_dim, ), std=LinearSchedule(0.2))
    config.min_memory_size = int(1e4)
    config.target_network_mix = 1e-3
    config.logger = get_logger(tag=kwargs['tag'])
    run_steps(DDPGAgent(config))


def ucb_ddpg_continuous(**kwargs):
    set_tag(kwargs)
    kwargs.setdefault('log_dir', get_default_log_dir(kwargs['tag']))
    kwargs.setdefault('gate', F.relu)
    kwargs.setdefault('weight_decay', 0)
    kwargs.setdefault('state_norm', False)
    kwargs.setdefault('num_actors', 6)
    kwargs.setdefault('num_critics', 10)
    kwargs.setdefault('bootstrap_prob', 0.5)
    kwargs.setdefault('std_weight', [1, 0.8, 0.6, 0.4, 0.2, 0])
    kwargs.setdefault('skip', False)
    config = Config()
    config.merge(kwargs)

    config.task_fn = lambda: Task(kwargs['game'])
    config.eval_env = Task(kwargs['game'], log_dir=kwargs['log_dir'])
    config.max_steps = int(2e6)
    config.eval_interval = int(1e4)
    config.eval_episodes = 20

    if kwargs['state_norm']:
        config.state_normalizer = MeanStdNormalizer()

    config.network_fn = lambda: EnsembleDeterministicActorCriticNet(
        config.state_dim, config.action_dim,
        num_actors=config.num_actors,
        num_critics=config.num_critics,
        actor_body=FCBody(config.state_dim, (400, 300), gate=kwargs['gate']),
        critic_body=TwoLayerFCBodyWithAction(
            config.state_dim, config.action_dim, (400, 300), gate=kwargs['gate']),
        actor_opt_fn=lambda params: torch.optim.Adam(params, lr=1e-4),
        critic_opt_fn=lambda params: torch.optim.Adam(params, lr=1e-3, weight_decay=kwargs['weight_decay']))

    config.replay_fn = lambda: Replay(memory_size=int(1e6), batch_size=64)
    config.discount = 0.99
    config.random_process_fn = lambda: OrnsteinUhlenbeckProcess(
        size=(config.action_dim, ), std=LinearSchedule(0.2))
    config.min_memory_size = int(1e4)
    config.target_network_mix = 1e-3
    config.logger = get_logger(tag=kwargs['tag'], skip=kwargs['skip'])
    run_steps(UCBDDPGAgent(config))


if __name__ == '__main__':
    mkdir('log')
    mkdir('data')
    random_seed()
    set_one_thread()
    select_device(-1)
    batch()
    # select_device(0)

    game = 'HalfCheetah-v2'
    # ucb_ddpg_continuous(game=game)
    # ddpg_continuous(game=game)
