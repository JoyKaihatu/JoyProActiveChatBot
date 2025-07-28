import { AppServer, AppSession } from "@mentra/sdk";
import axios from "axios";

/**
 * A custom keyword that triggers our action once detected in speech
 */
const ACTIVATION_PHRASE = "computer";

/**
 * VoiceActivationServer – an App that listens for final transcriptions and
 * reacts when the user utters the ACTIVATION_PHRASE.
 */

async function sendChatMessage(userId: string, message: string) {
    const response = await axios.post("http://localhost:8000/chat", {
    user_id: userId,
    user_message: message
    
    });

    console.log("Bot Reply : ", response.data);
    return response.data;
}


class VoiceActivationServer extends AppServer {
  /**
   * onSession is called automatically whenever a user connects.
   *
   * @param session   – Connection-scoped helper APIs and event emitters
   * @param sessionId – Unique identifier for this connection
   * @param userId    – MentraOS user identifier
   */



  protected async onSession(
    session: AppSession,
    sessionId: string,
    userId: string,
  ): Promise<void> {
    session.logger.info(`🔊  Session ${sessionId} started for ${userId}`);

    // 1️⃣  Subscribe to speech transcriptions
    const unsubscribe = session.events.onTranscription((data) => {
      // 2️⃣  Ignore interim results – we only care about the final text
      if (!data.isFinal) return;

      
      type GeminiOutput= {
        shouldRespond: boolean;
        responseText : string;
      }
      // 3️⃣  Normalize casing & whitespace for a simple comparison
      const spokenText = data.text.toLowerCase().trim();
      session.logger.debug(`Heard: "${spokenText}"`);

      session.layouts.showTextWall("thinking...", {durationMs: 1000});

      const reply = sendChatMessage(userId, spokenText);

      let reply_clean:GeminiOutput = reply;

      session.logger.info(`Bot Reply: "${reply_clean}"`);

      session.layouts.showTextWall(String(reply_clean.responseText),{durationMs: 7000});



      // 4️⃣  Check for the activation phrase
    //   if (spokenText.includes(ACTIVATION_PHRASE)) {
    //     session.logger.info("✨ Activation phrase detected!");

    //     // 5️⃣  Do something useful – here we show a text overlay
    //     session.layouts.showTextWall("👋 How can I help?");
    //     session.logger.info("✨ Show Text Sent");
    //   }


    });

    // 6️⃣  Clean up the listener when the session ends
    this.addCleanupHandler(unsubscribe);
  }
}

// Bootstrap the server using environment variables for configuration
new VoiceActivationServer({
  packageName: process.env.PACKAGE_NAME ?? "com.example.voiceactivation",
  apiKey: process.env.MENTRAOS_API_KEY!,
  port: Number(process.env.PORT ?? "3000"),
}).start();