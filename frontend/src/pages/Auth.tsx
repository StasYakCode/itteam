const Auth = () => {
  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center">
      <div className="bg-[#111111]/80 backdrop-blur-xl border border-white/5 rounded-xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-white text-center mb-6">Вхід</h1>
        <form className="space-y-4">
          <div>
            <label className="block text-gray-400 mb-2">Email</label>
            <input
              type="email"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-accent-blue focus:outline-none"
              placeholder="your@email.com"
            />
          </div>
          <div>
            <label className="block text-gray-400 mb-2">Пароль</label>
            <input
              type="password"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-accent-blue focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-accent-blue hover:bg-accent-blue/80 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            Увійти
          </button>
        </form>
      </div>
    </div>
  );
};

export default Auth;