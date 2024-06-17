<template>
  <v-app id="inspire">
    -- <v-app-bar
      class="px-3"
      density="compact"
      flat
    >
      <v-spacer></v-spacer>
      <div>PodCastReader</div>
      <v-spacer></v-spacer>
    </v-app-bar>
                                               
    <v-main class="bg-grey-lighten-3">
      <v-container>
        <v-row>
          <v-col
            cols="12"
            md="2"
          >
            <v-sheet class="sticky-div"
              min-height="268"
              rounded="lg"
            >
              <v-card
                class="mx-auto"
                max-width="300"
              >
                <!-- <v-list :items="podlist"></v-list> -->
                <v-list>
                  <v-list-item
                    title="FeedList"
                  ></v-list-item>
                  <v-divider></v-divider>
                  <v-list-item
                    v-for="item in podlist"
                    :key="item.title"
                    :title="item.title"
                    :value="item.value"
                    @click="onPodlistClick(item)"
                  >
                    <v-tooltip activator="parent" location="top">
                      <span>{{ item.title }}</span>
                    </v-tooltip>
                  </v-list-item>
                </v-list>
              </v-card>
            </v-sheet>
          </v-col>

          <v-col
            cols="12"
            md="2"
          >
            <v-sheet class="sticky-div"
              min-height="240"
              rounded="lg"
            >
              <v-card
                class="mx-auto"
                max-width="400"
              >
                <!-- <v-list :items="itemlist"></v-list> -->
                <v-list :max-height="480"  style="overflow-y: auto;">
                  <v-list-item
                    title="EpisodeList"
                  ></v-list-item>
                  <v-divider></v-divider>
                  <v-list-item
                    v-for="item in itemlist"
                    :key="item.title"
                    :title="item.title"
                    :value="item.value"
                    @click="onItemlistClick(item)"
                  >
                    <v-tooltip activator="parent" location="top">
                      <span>{{ item.title }}</span>
                    </v-tooltip>                  
                  </v-list-item>
                </v-list>
              </v-card>
            </v-sheet>
          </v-col>

          <v-col
            cols="12"
            md="8"
          >
            <v-sheet
              min-height="75vh"
              rounded="lg"
            >
              <!--  -->
              <h2>{{ cur_item.title }}</h2>
              <p>{{ cur_item.pubdate }}</p>
              <p><span v-html="cur_item.description"></span></p>
              <br>
              <h2 v-if="(subtitle.length == 0)&&(cur_item.title!=undefined)">未能找到字幕，请通过后台生成。</h2>
              <div class="container100">
                <template v-for="sub in subtitle">
                  <p :id="`sub${sub.start}`" >{{ sub.interval }}</p>
                  <blockquote :id="`subtitle${sub.start}`" >{{ sub.text }}</blockquote>
                </template>
              </div>
            </v-sheet>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
    <v-footer
      height="60"
      app
    >
      <audio controls ref="audioElement" @error="handleAudioError"  @timeupdate="handleTimeUpdate">
        <source :src="audiosrc" type="audio/mpeg" >
      </audio>
    </v-footer>
  </v-app>
</template>


<script setup>

import axios from 'axios'
import {parseOPML} from '@/utils/opml'
import { extractFromXml } from '@extractus/feed-extractor'
import CryptoJS from 'crypto-js';

import { ref,nextTick } from 'vue'


const audioElement = ref(null);

let podlist = ref([])
let itemlist = ref([])
let cur_item = ref({})
let audiosrc = ref('')
let audio_original_src = ref('')
let subtitle = ref([])
let cur_folder = ''

// 初始化
initMain()

// 点击itemlist时触发

// 初始化
function initMain(){
  //读取public/data/base.opml文件
  axios.get('data/base.opml').then(response => {
    const baseopml = response.data
    //console.log(baseopml)
    let opmljson = parseOPML(baseopml)
    console.log(opmljson)
    opmljson.forEach(element => {
      podlist.value.push({
        title: element.title,
        value: element.xmlUrl})
    });
  })
  itemlist.value = [];
}

//点击podlist时触发
async function  onPodlistClick(item){
  console.log(item)
  itemlist.value = [];
  //将value编码为md5
  const md5Hash = CryptoJS.MD5(item.title).toString();
  cur_folder = md5Hash;
  axios.get(`data/rss/${md5Hash}`).then(response => {
    const rss = response.data
    const feed = extractFromXml(rss,{getExtraEntryFields: (feedEntry) => {
      const {
        enclosure
      } = feedEntry
      return {
        enclosure: {
          url: enclosure['@_url'],
          type: enclosure['@_type'],
          length: enclosure['@_length']
        }
      }
    }})
    //解析feed
    feed.entries=feed.entries.slice(0, 100);
    feed.entries.forEach(element => {
      //console.log(element);
      if (element.link.toLowerCase().endsWith('.mp3')) {
        itemlist.value.push({
          title: element.title,
          description: element.description,
          pubdate: element.published,
          value: element.link})
      } else{
        itemlist.value.push({
          title: element.title,
          description: element.description,
          pubdate: element.published,
          value: element.enclosure.url})
      }
    });
    //console.log(itemlist.value)
  })
}

//点击itemlist时触发
function  onItemlistClick(item){
  cur_item.value = item
  console.log(item)
  audio_original_src.value = item.value
  //CryptoJS.MD5(item.title).toString()
  audiosrc.value = `data/mp3/${cur_folder}/${CryptoJS.MD5(item.title).toString()}.mp3`
  // nextTick(() => {
  //   // 重置音频元素
  //   audioElement.value.load();
  // });
  audioElement.value.load();
  handleSubtitles(`data/subtitles/${cur_folder}/${CryptoJS.MD5(item.title).toString()}.json`);
}

function handleAudioError() {
  console.log('音频加载失败，重新设置音频源')
  audiosrc.value = audio_original_src.value;
  nextTick(() => {
    // 重置音频元素
    audioElement.value.load();
  });
}

//处理播客脚本显示
function handleSubtitles(filepath){
  axios.get(filepath).then(response => {
    const json = response.data
    if (typeof(json) == 'object'){
      subtitle.value = json
    }else{
      subtitle.value = []
    }
  })
}


// 使用二分查找找到当前时间对应的字幕
function findSubtitle(subtitles, currentTime) {
    var left = 0;
    var right = subtitles.length - 1;
    while (left <= right) {
        var mid = Math.floor((left + right) / 2);
        if (subtitles[mid].start <= currentTime && currentTime <= subtitles[mid].end) {
            return subtitles[mid];
        } else if (currentTime < subtitles[mid].start) {
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    return null;
}

//
function handleTimeUpdate() {
  if (audioElement.value) {
    let currentTime = audioElement.value.currentTime;
    console.log(audioElement.value.currentTime)
    const currentSubtitle = findSubtitle(subtitle.value, currentTime);
    if (currentSubtitle) {
        //滚动到对应字幕
        //document.getElementById(`sub${currentSubtitle.start}`).scrollIntoView();
        scrollToElementCenter(`sub${currentSubtitle.start}`)
        document.querySelectorAll('blockquote').forEach(blockquote => {
          blockquote.classList.remove('bold-text');
        })
        document.getElementById(`subtitle${currentSubtitle.start}`).classList.add('bold-text');
    } else {
        console.log('当前时间: ' + currentTime + ', 无字幕显示');
        // 在这里清除或隐藏字幕
    }
  }
}

// 假设元素的ID为"elementId"
function scrollToElementCenter(elementId) {
  // 获取元素
  var element = document.getElementById(elementId);

  // 获取元素的高度
  var elementHeight = element.offsetHeight;

  // 获取视口的高度
  var viewportHeight = window.innerHeight || document.documentElement.clientHeight;

  // 计算元素到窗口顶部的距离
  var elementTop = element.offsetTop;

  // 计算滚动位置（使元素位于视口中央）
  var scrollPosition = elementTop - (viewportHeight / 3) + (elementHeight / 3);

  // 滚动到指定位置
  window.scrollTo({
    top: scrollPosition,
    behavior: 'smooth' // 平滑滚动
  });
}



</script>

<style>
  .container100 {
    width: 100%; /* 确保父元素宽度为 100% */
    /* 其他样式 */
  }
  .padding-top{
    padding-top: 60px; /* 根据需要调整这个值 */
    margin-top: -60px; /* 这个值需要和上面的padding-top相同，但是为负值 */
  }
  .sticky-div {
    position: sticky;
    top: 90px; /* 根据需要调整 */
    z-index: 1000; /* 确保固定div在顶部 */
  }
  audio {
    width: 100%; /* 让音频元素的宽度铺满父元素 */
  }
  blockquote {
    background: #f9f9f9;
    border-left: 5px solid #ccc;
    padding: 10px;
    margin: 5px 0;
  }
  .bold-text {
    font-weight: bold;
  }

</style>