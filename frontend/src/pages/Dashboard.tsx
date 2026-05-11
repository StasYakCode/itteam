const Dashboard = () => {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-8">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-[#111111]/80 backdrop-blur-xl border border-white/5 rounded-xl p-6">
          <h3 className="text-white font-semibold mb-2">Мої команди</h3>
          <p className="text-gray-400">2 активні команди</p>
        </div>
        <div className="bg-[#111111]/80 backdrop-blur-xl border border-white/5 rounded-xl p-6">
          <h3 className="text-white font-semibold mb-2">Проєкти</h3>
          <p className="text-gray-400">5 активних проєктів</p>
        </div>
        <div className="bg-[#111111]/80 backdrop-blur-xl border border-white/5 rounded-xl p-6">
          <h3 className="text-white font-semibold mb-2">Повідомлення</h3>
          <p className="text-gray-400">3 непрочитаних</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;