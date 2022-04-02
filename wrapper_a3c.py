# -*- coding: utf-8 -*-
"""Wrapper - A3C.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UwjEjsdvU7RgTRReknCGobKrFmvx5xqT
"""

class A3C:


 def __init__(self, model, env, weights = None, logs_path = None, weights_path = None):

   self.model = model
   self.environment = env
   self.behaviour_name = list(self.environment.behavior_specs)[0]
   self.spec = self.environment.behavior_specs[self.behavior_name]
   self.weights = weights
   self.logs_path = logs_path
   self.wheights_path = wheights_path
   


  def train(self):
    #==================== GLOBAL VARIABLES =====================
    SEED = 22
    EPISODES = 5000
    STEPS = 64
    VALUE_LOSS_COEF = 0.5
    GAMMA = 0.99
    MODEL_PATH = "/content/modelo/unity_actor_critic.pth"

    #==================== MODEL =====================


    model.train()

    optimizer = optim.Adam(model.parameters(), lr=0.001)
    tracked_agent=-1
    save = 0

    self.environment.reset()
    decision_steps, terminal_steps = self.environment.get_steps(self.behavior_name)

    print(f"Actual tracked agent = {tracked_agent}")
    if tracked_agent == -1 and len(decision_steps) >= 1:
          print(f"agents = {len(decision_steps)}")
          tracked_agent = decision_steps.agent_id[0]
          print(f"New tracked agent = {tracked_agent}")

    decision_steps, terminal_steps = self.environment.get_steps(self.behavior_name)
    obs = decision_steps[tracked_agent].obs
    state = torch.from_numpy(np.array(decision_steps[tracked_agent].obs)).float()
    total_values = []

    for ep in range(int(EPISODES)):
        self.environment.reset()
        decision_steps, terminal_steps = self.environment.get_steps(self.behavior_name)
        tracked_agent = -1 # -1 indicates not yet tracking
        done = False

        values = []
        log_probs = []
        rewards = []

        while not done:
            if tracked_agent == -1 and len(decision_steps) >= 1:
              print(f"agents = {len(decision_steps)}")
              tracked_agent = decision_steps.agent_id[0]

            #print(f"state = {state}")
            logits, value = model(state)

            prob = F.softmax(logits, -1)

            # Check if continuous or discrete
            if self.spec.action_spec.continuous_size > 0:  
              action = prob.multinomial(num_samples=self.spec.action_spec.continuous_size) # num samples será el numero de acciones
            else:
              action = prob.multinomial(num_samples=self.spec.action_spec.discrete_size)
            #print(f"raw action = {action}")
            log_prob = F.log_softmax(logits, -1)
            #print(f"log_prob = {log_prob}")
            log_prob = log_prob.gather(1, action)

            action_unity = ActionTuple()
            #print(f"action = {action}")

            if self.spec.action_spec.continuous_size > 0: 
              action_unity.add_continuous(np.array(action))
            else:
              action_unity.add_discrete(np.array(action))

            # Set the actions
            # env.set_actions(behavior_name, action_unity)
            self.environment.set_action_for_agent(self.behavior_name, tracked_agent, action_unity)
            self.environment.step()

            decision_steps, terminal_steps = self.environment.get_steps(self.behavior_name)
            if tracked_agent in decision_steps:  #not done
                obs = decision_steps[tracked_agent].obs
                reward = decision_steps[tracked_agent].reward
                done = False

            if tracked_agent in terminal_steps:  # done
                reward = terminal_steps[tracked_agent].reward
                done = True

            reward = np.clip(1, -1, reward)
            #print(f"calculated reward = {reward}")
            state = torch.from_numpy(np.array(obs)).float()

            values.append(value)
            log_probs.append(log_prob)
            rewards.append(reward)

            total_values.append(value.item())

            if done:
                break

        print(f"Suma de recompensas = {np.sum(rewards)}, media de total_values =  {np.mean(total_values)}")
        print("=========== ACTUALIZANDO MODELO ===========")
        ###################################
        ### Prepare for update the policy
        ###################################

        R = 0
        if not done:
            _, value = model(state)
            R = value.data

        values.append(R)
        policy_loss = 0
        value_loss = 0
        for i in reversed(range(len(rewards))):
            R = GAMMA * R + rewards[i]
            advantage = R - values[i]
            value_loss = value_loss + 0.5 * advantage.pow(2)
            policy_loss = policy_loss - (log_probs[i] * Variable(advantage))

        optimizer.zero_grad()
        loss_fn = (policy_loss + VALUE_LOSS_COEF * value_loss)
        #print(f"loss_fn = {loss_fn}")
        loss_fn.sum().backward(retain_graph=True)
        optimizer.step()
        if save % 1000 == 0:
            torch.save(model.state_dict(), MODEL_PATH)
        save +=1
        print(f"Episodio = {ep}")